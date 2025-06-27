"""
ChatCapability - Empathetic AI Companion

Provides emotional support, natural conversation, and warm companionship.
This is the CRITICAL capability that makes Encore AI empathetic and supportive.

Uses Claude Sonnet for more nuanced, contextual responses.
"""

import os
import httpx
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from capabilities.base import BaseCapability, CapabilityDescription
from models.capabilities import (
    ChatInputs, ChatResult, EmotionalContext, UserContext, 
    CapabilityInputs, CapabilityResult
)


class ChatCapability(BaseCapability):
    """AI companion for emotional support and conversation"""
    
    def __init__(self, api_key: str = None, model: str = None, use_anthropic: bool = True):
        self.use_anthropic = use_anthropic
        
        if use_anthropic:
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("Anthropic API key required for chat capability")
            # Use Claude Sonnet for chat
            self.model = model or os.getenv("LLM_CHAT_STANDARD", "claude-sonnet-4-20250514")
            self.api_url = "https://api.anthropic.com/v1/messages"
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key required for chat capability")
            self.model = model or os.getenv("LLM_TIER_STANDARD", "gpt-4o-mini")
            self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def describe(self) -> CapabilityDescription:
        """Describe chat capability for orchestrator"""
        return CapabilityDescription(
            name="Chat",
            purpose="Provide companionship, emotional support, and natural conversation for theater and Broadway professionals",
            inputs={
                "message": "User's message or emotional expression",
                "emotional_context": "Detected emotional state and support needs",
                "conversation_history": "Previous messages for context",
                "user_context": "User's role, organization, and preferences"
            },
            outputs={
                "response": "Warm, empathetic response with emotional support",
                "follow_up_questions": "Suggested questions to continue conversation",
                "emotional_tone": "Emotional tone of the response",
                "support_provided": "Whether emotional support was given"
            },
            examples=[
                "I'm feeling overwhelmed with these numbers",
                "This is stressful, help me understand what to focus on",
                "Tell me something positive about our performance",
                "What should I be looking at next?",
                "Tell me about the theater industry"
            ]
        )
    
    async def execute(self, inputs: CapabilityInputs) -> CapabilityResult:
        """Execute chat with emotional support"""
        if not isinstance(inputs, ChatInputs):
            raise ValueError(f"Expected ChatInputs, got {type(inputs)}")
        
        # Build context-aware prompt
        prompt = self._build_chat_prompt(inputs)
        
        # Generate empathetic response
        response_data = await self._generate_response(prompt, inputs)
        
        # Parse and return result
        return self._parse_response(response_data, inputs)
    
    def _build_chat_prompt(self, inputs: ChatInputs) -> str:
        """Build empathetic chat prompt with industry context"""
        
        # Use provided user context or defaults
        if inputs.user_context:
            user_context = {
                "industry": inputs.user_context.industry or "theater",
                "role": inputs.user_context.role or "theater professional",
                "organization": inputs.user_context.organization or "theater organization"
            }
        else:
            user_context = {
                "industry": "theater",
                "role": "theater professional",
                "organization": "theater organization"
            }
        
        # Emotional context analysis
        emotional_context = ""
        if inputs.emotional_context.support_needed:
            emotional_context = f"""
The user needs emotional support:
- Stress level: {inputs.emotional_context.stress_level or 'unknown'}
- Emotional tone: {inputs.emotional_context.tone or 'mixed'}

Provide brief, warm support first. Keep responses concise but caring.
"""
        
        # Conversation history
        history_context = ""
        if inputs.conversation_history:
            recent_messages = inputs.conversation_history[-3:]  # Last 3 messages
            history_context = "Recent conversation:\n"
            for msg in recent_messages:
                role = "User" if msg.role == "user" else "Assistant"
                history_context += f"{role}: {msg.content[:100]}...\n"
        
        # Check if 10+ messages - suggest preferences update
        suggest_preferences = len(inputs.conversation_history) >= 10 and len(inputs.conversation_history) % 10 == 0
        
        return f"""
You are an empathetic AI companion for {user_context['industry']} professionals. The user works as a {user_context['role']} at a {user_context['organization']}.

Your personality:
- Warm and genuinely caring but concise
- Deep understanding of {user_context['industry']} pressures and dynamics
- Supportive without overdoing it - match the emotional level needed
- Knowledgeable about Broadway, touring, audience development, ticketing
- Professional but personable

{emotional_context}

{history_context}

Guidelines:
1. Keep responses SHORT - 2-3 sentences max unless explaining something specific
2. Only provide emotional support if actually needed - don't overdo it
3. For neutral questions, give direct, helpful answers
4. Use industry-specific language (shows, productions, houses, etc.)
5. NEVER make claims about data without verification (e.g., don't say "X is your strongest show")
6. When user feels overwhelmed, guide them toward specific metrics we can analyze
7. Be mindful of corporate context - avoid suggesting career changes or role exploration
8. If asked what to focus on, acknowledge you need more context about their priorities
{"9. Subtly suggest: 'By the way, would it help if I understood your specific role and preferences better?'" if suggest_preferences else ""}

Current message: "{inputs.message}"

Respond with JSON:
{{
    "response": "Your concise response (2-3 sentences)",
    "follow_up_questions": ["1-2 relevant questions"],
    "emotional_tone": "supportive|encouraging|conversational|professional",
    "support_provided": true/false
}}

Match the user's emotional level - don't be overly supportive for neutral questions.
"""
    
    async def _generate_response(self, prompt: str, inputs: ChatInputs) -> Dict[str, Any]:
        """Generate response using Claude or OpenAI"""
        
        if self.use_anthropic:
            return await self._generate_claude_response(prompt)
        else:
            return await self._generate_openai_response(prompt)
    
    async def _generate_claude_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using Claude API"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": 400,
                    "temperature": 0.7,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["content"][0]["text"]
            
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError):
                # Fallback
                return {
                    "response": content[:200],  # Limit length
                    "follow_up_questions": [],
                    "emotional_tone": "conversational",
                    "support_provided": False
                }
    
    async def _generate_openai_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using OpenAI API (fallback)"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a concise AI companion for theater professionals. Respond with brief, helpful JSON."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 400
                }
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "response": content[:200],
                    "follow_up_questions": [],
                    "emotional_tone": "conversational",
                    "support_provided": False
                }
    
    def _parse_response(self, response_data: Dict[str, Any], inputs: ChatInputs) -> ChatResult:
        """Parse LLM response into ChatResult"""
        
        # Ensure follow-up questions are limited
        follow_ups = response_data.get("follow_up_questions", [])[:2]
        
        return ChatResult(
            response=response_data.get("response", "I'm here to help."),
            follow_up_questions=follow_ups,
            emotional_tone=response_data.get("emotional_tone", "conversational"),
            support_provided=response_data.get("support_provided", inputs.emotional_context.support_needed),
            success=True,
            metadata={
                "model_used": self.model,
                "provider": "anthropic" if self.use_anthropic else "openai",
                "emotional_context_detected": inputs.emotional_context.model_dump(),
                "conversation_length": len(inputs.conversation_history)
            }
        )