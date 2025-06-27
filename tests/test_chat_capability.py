"""
Tests for ChatCapability - Empathetic AI Companion

Run: docker-compose run --rm test python -m pytest tests/test_chat_capability.py -v -s
"""

import pytest
from datetime import datetime
from typing import List

from capabilities.chat import ChatCapability
from models.capabilities import ChatInputs, EmotionalContext
from models.state import Message


class TestChatCapability:
    """Test the empathetic chat capability"""
    
    @pytest.fixture
    def chat_capability(self):
        """Create chat capability instance"""
        # Try Anthropic first, then OpenAI, then fail
        import os
        if os.getenv("ANTHROPIC_API_KEY"):
            return ChatCapability(use_anthropic=True)
        elif os.getenv("OPENAI_API_KEY"):
            return ChatCapability(use_anthropic=False)
        else:
            pytest.skip("No API keys available")
    
    @pytest.mark.asyncio
    async def test_emotional_support_response(self, chat_capability):
        """Test emotional support for overwhelmed user"""
        
        inputs = ChatInputs(
            session_id="test_session",
            tenant_id="test_tenant",
            user_id="test_user",
            message="I'm feeling overwhelmed with all these numbers",
            emotional_context=EmotionalContext(
                tone="stressed",
                support_needed=True,
                stress_level="high",
                confidence_level="low"
            ),
            conversation_history=[]
        )
        
        result = await chat_capability.execute(inputs)
        
        print(f"\n🧪 Testing Emotional Support Response")
        print(f"Input: {inputs.message}")
        print(f"Response: {result.response}")
        print(f"Follow-ups: {result.follow_up_questions}")
        print(f"Emotional tone: {result.emotional_tone}")
        print(f"Support provided: {result.support_provided}")
        
        assert result.success == True
        assert result.support_provided == True
        assert len(result.response) > 0
        assert result.emotional_tone in ["supportive", "understanding", "encouraging"]
        
        # Check that response is empathetic
        response_lower = result.response.lower()
        assert any(word in response_lower for word in [
            "understand", "feel", "overwhelming", "support", "here", "help"
        ]), "Response should show empathy"
    
    @pytest.mark.asyncio
    async def test_conversational_response(self, chat_capability):
        """Test conversational response about theater industry"""
        
        inputs = ChatInputs(
            session_id="test_session",
            tenant_id="test_tenant", 
            user_id="test_user",
            message="Tell me about the theater industry",
            emotional_context=EmotionalContext(
                tone="curious",
                support_needed=False,
                stress_level="low",
                confidence_level="medium"
            ),
            conversation_history=[]
        )
        
        result = await chat_capability.execute(inputs)
        
        print(f"\n🎭 Testing Conversational Response")
        print(f"Input: {inputs.message}")
        print(f"Response: {result.response}")
        print(f"Follow-ups: {result.follow_up_questions}")
        print(f"Emotional tone: {result.emotional_tone}")
        
        assert result.success == True
        assert len(result.response) > 0
        assert len(result.follow_up_questions) > 0
        assert result.emotional_tone in ["conversational", "supportive", "encouraging"]
        
        # Check that response mentions theater/Broadway
        response_lower = result.response.lower()
        assert any(word in response_lower for word in [
            "theater", "theatre", "broadway", "entertainment", "audience", "show"
        ]), "Response should be relevant to theater industry"
    
    @pytest.mark.asyncio
    async def test_follow_up_generation(self, chat_capability):
        """Test follow-up question generation"""
        
        inputs = ChatInputs(
            session_id="test_session",
            tenant_id="test_tenant",
            user_id="test_user", 
            message="What should I focus on today?",
            emotional_context=EmotionalContext(
                tone="uncertain",
                support_needed=False,
                stress_level="medium",
                confidence_level="low"
            ),
            conversation_history=[]
        )
        
        result = await chat_capability.execute(inputs)
        
        print(f"\n🎯 Testing Follow-up Generation")
        print(f"Input: {inputs.message}")
        print(f"Response: {result.response}")
        print(f"Follow-ups: {result.follow_up_questions}")
        
        assert result.success == True
        assert len(result.follow_up_questions) >= 1
        assert len(result.follow_up_questions) <= 3  # Reasonable number
        
        # Check follow-ups are questions
        for question in result.follow_up_questions:
            assert question.endswith("?"), f"Follow-up should be a question: {question}"
    
    @pytest.mark.asyncio 
    async def test_conversation_context(self, chat_capability):
        """Test conversation history context"""
        
        # Previous conversation
        history = [
            Message(
                id="msg1",
                role="user",
                content="I'm looking at our Chicago numbers",
                timestamp=datetime.now()
            ),
            Message(
                id="msg2",
                role="assistant", 
                content="Chicago is one of our strongest shows. What specific metrics are you interested in?",
                timestamp=datetime.now()
            )
        ]
        
        inputs = ChatInputs(
            session_id="test_session",
            tenant_id="test_tenant",
            user_id="test_user",
            message="The attendance seems low this week",
            emotional_context=EmotionalContext(
                tone="concerned",
                support_needed=False,
                stress_level="medium"
            ),
            conversation_history=history
        )
        
        result = await chat_capability.execute(inputs)
        
        print(f"\n💬 Testing Conversation Context")
        print(f"Previous context: Chicago discussion")
        print(f"Input: {inputs.message}")
        print(f"Response: {result.response}")
        
        assert result.success == True
        assert len(result.response) > 0
        
        # Response should acknowledge context about Chicago
        response_lower = result.response.lower()
        assert "chicago" in response_lower, "Response should reference Chicago from context"
    
    @pytest.mark.unit
    def test_capability_description(self, chat_capability):
        """Test capability describes itself correctly"""
        
        description = chat_capability.describe()
        
        print(f"\n📋 Testing Capability Description")
        print(f"Name: {description.name}")
        print(f"Purpose: {description.purpose}")
        print(f"Examples: {description.examples}")
        
        assert description.name == "Chat"
        assert "emotional support" in description.purpose.lower()
        assert "companionship" in description.purpose.lower()
        assert len(description.examples) >= 3
        assert len(description.inputs) >= 3
        assert len(description.outputs) >= 3
    
    @pytest.mark.unit
    def test_input_validation(self, chat_capability):
        """Test input validation"""
        
        # Test invalid input type
        with pytest.raises(ValueError, match="Expected ChatInputs"):
            # Create a mock input that's not ChatInputs
            class MockInputs:
                pass
            
            # This should be awaited in real usage, but for test we just check the sync validation
            try:
                import asyncio
                asyncio.run(chat_capability.execute(MockInputs()))
            except ValueError as e:
                assert "Expected ChatInputs" in str(e)
                raise  # Re-raise for pytest to catch
    
    @pytest.mark.asyncio
    async def test_multiple_emotional_scenarios(self, chat_capability):
        """Test various emotional scenarios"""
        
        scenarios = [
            {
                "message": "This is really stressful, I don't know what to do",
                "emotional_context": EmotionalContext(
                    tone="anxious",
                    support_needed=True,
                    stress_level="high"
                ),
                "expected_support": True
            },
            {
                "message": "Tell me something positive about our performance",
                "emotional_context": EmotionalContext(
                    tone="seeking_reassurance",
                    support_needed=True,
                    confidence_level="low"
                ),
                "expected_support": True
            },
            {
                "message": "How has your day been?",
                "emotional_context": EmotionalContext(
                    tone="friendly",
                    support_needed=False
                ),
                "expected_support": False
            }
        ]
        
        print(f"\n🎭 Testing Multiple Emotional Scenarios")
        
        for i, scenario in enumerate(scenarios, 1):
            inputs = ChatInputs(
                session_id="test_session",
                tenant_id="test_tenant", 
                user_id="test_user",
                message=scenario["message"],
                emotional_context=scenario["emotional_context"],
                conversation_history=[]
            )
            
            result = await chat_capability.execute(inputs)
            
            print(f"\nScenario {i}:")
            print(f"  Input: {scenario['message']}")
            print(f"  Expected support: {scenario['expected_support']}")
            print(f"  Actual support: {result.support_provided}")
            print(f"  Response: {result.response[:100]}...")
            
            assert result.success == True
            assert len(result.response) > 0
            
            # Emotional scenarios should provide support
            if scenario["expected_support"]:
                assert result.support_provided == True
                assert result.emotional_tone in ["supportive", "understanding", "encouraging"]