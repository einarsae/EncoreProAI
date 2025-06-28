"""
CubeMetaService - Discover entity types and dimensions from Cube.js schema

Fetches Cube.js meta schema to dynamically discover:
- What entity types exist (productions, venues, customers, etc.)
- What dimensions represent IDs and names for each entity type
- What measures are available

Based on old system but simplified for our needs.
"""

import httpx
from typing import List, Dict, Optional
import logging
import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CubeMetaService:
    """Discover entity configuration from Cube.js meta schema"""
    
    def __init__(self, cube_url: str, cube_secret: str):
        self.cube_url = cube_url
        self.cube_secret = cube_secret
        self._meta: Optional[Dict] = None
    
    def generate_token(self, tenant_id: str = "default") -> str:
        """Generate JWT token for meta API access"""
        payload = {
            "sub": tenant_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        return jwt.encode(payload, self.cube_secret, algorithm="HS256")
    
    async def refresh_meta(self):
        """Fetch Cube.js meta schema"""
        # Clean up URL to avoid double slashes
        base_url = self.cube_url.rstrip('/')
        meta_url = f"{base_url}/cubejs-api/v1/meta"
        
        # Generate JWT token for meta access
        token = self.generate_token()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                meta_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            self._meta = response.json()
        
        logger.info(f"Loaded Cube.js meta schema with {len(self._meta.get('cubes', []))} cubes")
    
    async def get_entity_types(self) -> List[str]:
        """Get list of entity types (cube names + fake entities) available"""
        if not self._meta:
            await self.refresh_meta()
        
        cubes = self._meta.get("cubes", [])
        entity_types = []
        
        # Real entity types (cubes with .id and .name)
        for cube in cubes:
            cube_name = cube.get("name", "")
            dimensions = cube.get("dimensions", [])
            dimension_names = [d.get("name", "") for d in dimensions]
            
            has_id = any(name.endswith(".id") for name in dimension_names)
            has_name = any(name.endswith(".name") for name in dimension_names)
            
            if has_id and has_name:
                if "." in cube_name:
                    entity_type = cube_name.split(".")[0]  
                else:
                    entity_type = cube_name
                
                if entity_type not in entity_types:
                    entity_types.append(entity_type)
        
        # Categorical entity types from ticket_line_items dimensions
        # These are geographical/categorical dimensions where id=name
        categorical_entities = ["city", "country", "state", "currency"]
        
        # Check if ticket_line_items exists and has these dimensions
        ticket_cube = next((c for c in cubes if c.get("name") == "ticket_line_items"), None)
        if ticket_cube:
            ticket_dimensions = [d.get("name", "") for d in ticket_cube.get("dimensions", [])]
            
            for categorical_entity in categorical_entities:
                dimension_name = f"ticket_line_items.{categorical_entity}"
                if dimension_name in ticket_dimensions:
                    entity_types.append(categorical_entity)
        
        logger.info(f"Discovered entity types: {entity_types}")
        return entity_types
    
    async def get_entity_config(self, entity_type: str) -> Optional[Dict[str, str]]:
        """Get ID and name dimensions for an entity type (real or categorical)"""
        if not self._meta:
            await self.refresh_meta()
        
        # Check if this is a categorical entity (geographical/categorical)
        categorical_entities = ["city", "country", "state","postcode"]
        if entity_type in categorical_entities:
            dimension_name = f"ticket_line_items.{entity_type}"
            config = {
                "id_dimension": dimension_name,    # id = name for categorical entities
                "name_dimension": dimension_name,  # name = value
                "cube_name": "ticket_line_items",
                "is_categorical": True
            }
            logger.info(f"Categorical entity config for {entity_type}: {config}")
            return config
        
        # Real entity type - look for cube with .id and .name
        cubes = self._meta.get("cubes", [])
        
        for cube in cubes:
            cube_name = cube.get("name", "")
            
            # Check if this cube matches the entity type
            if (cube_name == entity_type or 
                cube_name.startswith(f"{entity_type}.") or
                cube_name.endswith(f".{entity_type}")):
                
                dimensions = cube.get("dimensions", [])
                
                # Find ID and name dimensions
                id_dimension = None
                name_dimension = None
                
                for dim in dimensions:
                    dim_name = dim.get("name", "")
                    if dim_name.endswith(".id"):
                        id_dimension = dim_name
                    elif dim_name.endswith(".name"):
                        name_dimension = dim_name
                
                if id_dimension and name_dimension:
                    config = {
                        "id_dimension": id_dimension,
                        "name_dimension": name_dimension,
                        "cube_name": cube_name,
                        "is_categorical": False
                    }
                    logger.info(f"Real entity config for {entity_type}: {config}")
                    return config
        
        logger.warning(f"No entity config found for {entity_type}")
        return None
    
    async def get_all_dimensions(self) -> List[str]:
        """Get all dimension names across all cubes"""
        if not self._meta:
            await self.refresh_meta()
        
        dimensions = []
        cubes = self._meta.get("cubes", [])
        
        for cube in cubes:
            for dim in cube.get("dimensions", []):
                dim_name = dim.get("name", "")
                if dim_name and dim_name not in dimensions:
                    dimensions.append(dim_name)
        
        return sorted(dimensions)
    
    async def get_all_measures(self) -> List[str]:
        """Get all measure names across all cubes"""
        if not self._meta:
            await self.refresh_meta()
        
        measures = []
        cubes = self._meta.get("cubes", [])
        
        for cube in cubes:
            for measure in cube.get("measures", []):
                measure_name = measure.get("name", "")
                if measure_name and measure_name not in measures:
                    measures.append(measure_name)
        
        return sorted(measures)
    
    async def get_meta(self) -> Dict:
        """Get the raw meta schema"""
        if not self._meta:
            await self.refresh_meta()
        return self._meta or {}
    
    async def debug_schema(self) -> Dict:
        """Return full schema info for debugging"""
        if not self._meta:
            await self.refresh_meta()
        
        debug_info = {
            "cube_count": len(self._meta.get("cubes", [])),
            "cubes": []
        }
        
        for cube in self._meta.get("cubes", []):
            cube_info = {
                "name": cube.get("name"),
                "dimensions": [d.get("name") for d in cube.get("dimensions", [])],
                "measures": [m.get("name") for m in cube.get("measures", [])]
            }
            debug_info["cubes"].append(cube_info)
        
        return debug_info