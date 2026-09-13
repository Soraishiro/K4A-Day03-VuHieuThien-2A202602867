"""
Unit tests for providers.py - Multi-Provider LLM Adapter
"""
import pytest
from unittest.mock import patch, MagicMock
import os

from src.providers import (
    BaseLLMProvider,
    MockOfflineProvider,
    GeminiProvider,
    OpenAIProvider,
    get_llm_provider,
)


class TestBaseLLMProvider:
    """Test base provider interface"""

    def test_base_provider_abstract(self):
        provider = BaseLLMProvider()
        with pytest.raises(NotImplementedError):
            provider.generate("test")
        with pytest.raises(NotImplementedError):
            provider.generate_with_tools("test", [])


class TestMockOfflineProvider:
    """Test Mock Offline Provider"""

    def setup_method(self):
        self.provider = MockOfflineProvider()

    def test_model_name(self):
        assert self.provider.model_name == "Offline-Mock-Model-2026"

    def test_generate_returns_mock_response(self):
        response = self.provider.generate("Hello")
        assert isinstance(response, str)
        assert "[Mock Chatbot Response]" in response
        assert "Hello" in response

    def test_generate_with_tools_academic_query(self):
        response = self.provider.generate_with_tools(
            "Tra cứu SV2026001",
            [],
            system_prompt="",
            chat_history=[]
        )
        assert response["type"] == "tool_call"
        assert response["tool_name"] == "academic_query"
        assert response["arguments"]["student_id"] == "SV2026001"
        assert "thought" in response

    def test_generate_with_tools_schedule_appointment(self):
        response = self.provider.generate_with_tools(
            "Đặt lịch cho SV2026001 lúc 14:00 15/09/2026",
            [],
            system_prompt="",
            chat_history=[]
        )
        assert response["type"] == "tool_call"
        assert response["tool_name"] == "schedule_appointment"
        assert response["arguments"]["student_id"] == "SV2026001"
        assert response["arguments"]["datetime_str"] == "14:00 15/09/2026"
        assert response["arguments"]["advisor_name"] == "PGS.TS Nguyễn Văn A"

    def test_generate_with_tools_course_catalog(self):
        response = self.provider.generate_with_tools(
            "Thông tin môn Trí tuệ nhân tạo",
            [],
            system_prompt="",
            chat_history=[]
        )
        assert response["type"] == "tool_call"
        assert response["tool_name"] == "course_catalog_query"
        assert response["arguments"]["course_name"] == "Trí tuệ nhân tạo"

    def test_generate_with_tools_direct_answer(self):
        response = self.provider.generate_with_tools(
            "Quy chế tốt nghiệp cần bao nhiêu tín chỉ?",
            [],
            system_prompt="",
            chat_history=[]
        )
        assert response["type"] == "text"
        assert "content" in response
        assert "128" in response["content"]
        assert "thought" in response

    def test_generate_with_tools_chat_history(self):
        chat_history = [
            {"role": "assistant", "tool_name": "academic_query", "arguments": {"student_id": "SV2026001"}, "thought": "test", "tool_call_id": "call_1"},
            {"role": "tool", "tool_call_id": "call_1", "content": '{"status": "SUCCESS", "data": {"gpa": 3.85}}'}
        ]
        response = self.provider.generate_with_tools(
            "GPA của bạn ấy là bao nhiêu?",
            [],
            system_prompt="",
            chat_history=chat_history
        )
        # Should use chat history context
        assert "type" in response


class TestGeminiProvider:
    """Test Gemini Provider (mocked)"""

    def test_gemini_provider_init_without_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            provider = GeminiProvider(api_key="")
            assert provider.api_key == ""

    def test_gemini_provider_init_with_key(self):
        provider = GeminiProvider(api_key="test-key-123")
        assert provider.api_key == "test-key-123"

    def test_gemini_generate_without_key_returns_error(self):
        provider = GeminiProvider(api_key="")
        response = provider.generate("test")
        assert "[Gemini Error]" in response
        assert "GEMINI_API_KEY" in response

    def test_gemini_generate_with_tools_without_key_falls_back_to_mock(self):
        provider = GeminiProvider(api_key="")
        response = provider.generate_with_tools("Tra cứu SV2026001", [], "", [])
        # Should fall back to mock
        assert response["type"] == "tool_call"
        assert response["tool_name"] == "academic_query"

    @patch("google.genai.Client")
    def test_gemini_generate_with_tools_success(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.function_calls = []
        mock_response.text = "Direct answer from Gemini"
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key="valid-key")
        response = provider.generate_with_tools("test prompt", [], "", [])
        
        assert response["type"] == "text"
        assert response["content"] == "Direct answer from Gemini"

    @patch("google.genai.Client")
    def test_gemini_generate_with_tools_function_call(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        mock_call = MagicMock()
        mock_call.name = "academic_query"
        mock_call.args = {"student_id": "SV2026001"}
        
        mock_response = MagicMock()
        mock_response.function_calls = [mock_call]
        mock_response.text = None
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key="valid-key")
        response = provider.generate_with_tools("Tra cứu SV2026001", [], "", [])
        
        assert response["type"] == "tool_call"
        assert response["tool_name"] == "academic_query"
        assert response["arguments"]["student_id"] == "SV2026001"


class TestOpenAIProvider:
    """Test OpenAI Provider (mocked)"""

    def test_openai_provider_init_without_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            provider = OpenAIProvider(api_key="")
            assert provider.api_key == ""

    def test_openai_provider_init_with_key(self):
        provider = OpenAIProvider(api_key="test-key-123")
        assert provider.api_key == "test-key-123"

    def test_openai_generate_without_key_returns_error(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            provider = OpenAIProvider(api_key="")
            response = provider.generate("test")
        assert "[OpenAI Error]" in response
        assert "OPENAI_API_KEY" in response

    def test_openai_generate_with_tools_without_key_falls_back_to_mock(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            provider = OpenAIProvider(api_key="")
            response = provider.generate_with_tools("Tra cứu SV2026001", [], "", [])
        assert response["type"] == "tool_call"
        assert response["tool_name"] == "academic_query"

    @patch("openai.OpenAI")
    def test_openai_generate_with_tools_success(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_msg = MagicMock()
        mock_msg.tool_calls = None
        mock_msg.content = "Direct answer from OpenAI"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = OpenAIProvider(api_key="valid-key")
        response = provider.generate_with_tools("test prompt", [], "", [])
        
        assert response["type"] == "text"
        assert response["content"] == "Direct answer from OpenAI"

    @patch("openai.OpenAI")
    def test_openai_generate_with_tools_function_call(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_function = MagicMock()
        mock_function.name = "academic_query"
        mock_function.arguments = '{"student_id": "SV2026001"}'
        
        mock_call = MagicMock()
        mock_call.id = "call_123"
        mock_call.function = mock_function
        
        mock_msg = MagicMock()
        mock_msg.tool_calls = [mock_call]
        mock_msg.content = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = OpenAIProvider(api_key="valid-key")
        response = provider.generate_with_tools("Tra cứu SV2026001", [], "", [])
        
        assert response["type"] == "tool_call"
        assert response["tool_name"] == "academic_query"
        assert response["arguments"]["student_id"] == "SV2026001"
        assert response["tool_call_id"] == "call_123"


class TestGetLLMProvider:
    """Test provider factory function"""

    def test_get_gemini_provider(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "valid-key"}, clear=False):
            provider = get_llm_provider()
            assert isinstance(provider, GeminiProvider)

    def test_get_openai_provider(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "valid-key"}, clear=False):
            provider = get_llm_provider()
            assert isinstance(provider, OpenAIProvider)

    def test_get_mock_provider(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}, clear=False):
            provider = get_llm_provider()
            assert isinstance(provider, MockOfflineProvider)

    def test_get_unknown_provider_fallbacks_to_mock(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "unknown"}, clear=False):
            provider = get_llm_provider()
            assert isinstance(provider, MockOfflineProvider)

    def test_get_gemini_without_key_fallbacks_to_mock(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": ""}, clear=False):
            provider = get_llm_provider()
            assert isinstance(provider, MockOfflineProvider)

    def test_get_openai_without_key_fallbacks_to_mock(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": ""}, clear=False):
            provider = get_llm_provider()
            assert isinstance(provider, MockOfflineProvider)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])