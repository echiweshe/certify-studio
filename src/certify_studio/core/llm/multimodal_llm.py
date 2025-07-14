"""
Multimodal LLM integration with support for text, vision, and audio.
"""

from typing import Dict, List, Any, Optional, Union, AsyncIterator
from enum import Enum
from dataclasses import dataclass
import base64
from pathlib import Path
import asyncio
import json

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import anthropic
import openai
from PIL import Image
import numpy as np

from ..logging import get_logger
from ..config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class LLMProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC_CLAUDE = "anthropic_claude"
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT4_VISION = "openai_gpt4_vision"
    ANTHROPIC_CLAUDE_VISION = "anthropic_claude_vision"


@dataclass
class MultimodalMessage:
    """Message that can contain text, images, and audio."""
    text: Optional[str] = None
    images: List[Union[Path, Image.Image, np.ndarray]] = None
    audio: Optional[Union[Path, bytes]] = None
    role: str = "user"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MultimodalResponse:
    """Response from multimodal LLM."""
    text: str
    images: List[Dict[str, Any]] = None  # Generated images with metadata
    audio: Optional[bytes] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence_scores: Dict[str, float] = None
    reasoning_trace: List[str] = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.reasoning_trace is None:
            self.reasoning_trace = []


class MultimodalLLM:
    """Unified interface for multimodal LLM interactions."""
    
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.ANTHROPIC_CLAUDE_VISION,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        self.provider = provider
        self.model_name = model_name or self._get_default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize clients
        self._init_clients()
        
        # Vision and audio processors
        self.vision_processor = VisionProcessor()
        self.audio_processor = AudioProcessor()
    
    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            LLMProvider.ANTHROPIC_CLAUDE: "claude-3-opus-20240229",
            LLMProvider.ANTHROPIC_CLAUDE_VISION: "claude-3-opus-20240229",
            LLMProvider.OPENAI_GPT4: "gpt-4-turbo-preview",
            LLMProvider.OPENAI_GPT4_VISION: "gpt-4-vision-preview"
        }
        return defaults.get(self.provider, "claude-3-opus-20240229")
    
    def _init_clients(self):
        """Initialize LLM clients."""
        if self.provider in [LLMProvider.ANTHROPIC_CLAUDE, LLMProvider.ANTHROPIC_CLAUDE_VISION]:
            self.anthropic_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY.get_secret_value() if settings.ANTHROPIC_API_KEY else None
            )
            self.langchain_model = ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=settings.ANTHROPIC_API_KEY.get_secret_value() if settings.ANTHROPIC_API_KEY else None
            )
        elif self.provider in [LLMProvider.OPENAI_GPT4, LLMProvider.OPENAI_GPT4_VISION]:
            self.openai_client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
            )
            self.langchain_model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
            )
    
    async def generate(
        self,
        messages: List[MultimodalMessage],
        system_prompt: Optional[str] = None,
        stream: bool = False,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Union[MultimodalResponse, AsyncIterator[str]]:
        """Generate response from multimodal messages."""
        
        logger.info(f"Generating response with {self.provider.value}")
        
        # Process messages for the specific provider
        processed_messages = await self._process_messages(messages, system_prompt)
        
        if stream:
            return self._stream_response(processed_messages, response_format)
        else:
            return await self._generate_response(processed_messages, response_format)
    
    async def _process_messages(
        self,
        messages: List[MultimodalMessage],
        system_prompt: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Process multimodal messages for the provider."""
        
        processed = []
        
        # Add system prompt if provided
        if system_prompt:
            if self.provider in [LLMProvider.ANTHROPIC_CLAUDE, LLMProvider.ANTHROPIC_CLAUDE_VISION]:
                # Claude uses system parameter separately
                pass
            else:
                processed.append({
                    "role": "system",
                    "content": system_prompt
                })
        
        # Process each message
        for msg in messages:
            processed_msg = await self._process_single_message(msg)
            processed.append(processed_msg)
        
        return processed
    
    async def _process_single_message(
        self,
        message: MultimodalMessage
    ) -> Dict[str, Any]:
        """Process a single multimodal message."""
        
        if self.provider == LLMProvider.ANTHROPIC_CLAUDE_VISION:
            return await self._process_claude_vision_message(message)
        elif self.provider == LLMProvider.OPENAI_GPT4_VISION:
            return await self._process_gpt4_vision_message(message)
        else:
            # Text-only providers
            return {
                "role": message.role,
                "content": message.text or ""
            }
    
    async def _process_claude_vision_message(
        self,
        message: MultimodalMessage
    ) -> Dict[str, Any]:
        """Process message for Claude with vision."""
        
        content = []
        
        # Add text
        if message.text:
            content.append({
                "type": "text",
                "text": message.text
            })
        
        # Add images
        for image in message.images:
            image_data = await self.vision_processor.process_image(image)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_data["media_type"],
                    "data": image_data["base64"]
                }
            })
        
        # Add audio (convert to text description for now)
        if message.audio:
            audio_text = await self.audio_processor.transcribe(message.audio)
            content.append({
                "type": "text",
                "text": f"[Audio Transcript]: {audio_text}"
            })
        
        return {
            "role": message.role,
            "content": content
        }
    
    async def _process_gpt4_vision_message(
        self,
        message: MultimodalMessage
    ) -> Dict[str, Any]:
        """Process message for GPT-4 Vision."""
        
        content = []
        
        # Add text
        if message.text:
            content.append({
                "type": "text",
                "text": message.text
            })
        
        # Add images
        for image in message.images:
            image_data = await self.vision_processor.process_image(image)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_data['media_type']};base64,{image_data['base64']}"
                }
            })
        
        return {
            "role": message.role,
            "content": content
        }
    
    async def _generate_response(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]]
    ) -> MultimodalResponse:
        """Generate a complete response."""
        
        if self.provider == LLMProvider.ANTHROPIC_CLAUDE_VISION:
            response = await self._generate_claude_response(messages, response_format)
        elif self.provider == LLMProvider.OPENAI_GPT4_VISION:
            response = await self._generate_gpt4_response(messages, response_format)
        else:
            response = await self._generate_text_response(messages, response_format)
        
        return response
    
    async def _generate_claude_response(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]]
    ) -> MultimodalResponse:
        """Generate response using Claude."""
        
        try:
            # Extract system message if present
            system_msg = None
            user_messages = messages
            
            if messages and messages[0]["role"] == "system":
                system_msg = messages[0]["content"]
                user_messages = messages[1:]
            
            # Call Claude API
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_msg,
                messages=user_messages
            )
            
            # Parse response
            text_content = response.content[0].text if response.content else ""
            
            # Extract structured data if requested
            structured_data = None
            if response_format and response_format.get("type") == "json":
                structured_data = self._extract_json_from_text(text_content)
            
            # Extract confidence scores and reasoning
            confidence_scores = self._extract_confidence_scores(text_content)
            reasoning_trace = self._extract_reasoning_trace(text_content)
            
            return MultimodalResponse(
                text=text_content,
                structured_data=structured_data,
                confidence_scores=confidence_scores,
                reasoning_trace=reasoning_trace
            )
            
        except Exception as e:
            logger.error(f"Error generating Claude response: {e}")
            raise
    
    async def _generate_gpt4_response(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]]
    ) -> MultimodalResponse:
        """Generate response using GPT-4."""
        
        try:
            # Prepare request
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            if response_format:
                request_params["response_format"] = response_format
            
            # Call OpenAI API
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                **request_params
            )
            
            # Parse response
            text_content = response.choices[0].message.content
            
            # Extract structured data
            structured_data = None
            if response_format and response_format.get("type") == "json_object":
                structured_data = json.loads(text_content)
            
            return MultimodalResponse(
                text=text_content,
                structured_data=structured_data
            )
            
        except Exception as e:
            logger.error(f"Error generating GPT-4 response: {e}")
            raise
    
    async def _generate_text_response(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]]
    ) -> MultimodalResponse:
        """Generate text-only response using LangChain."""
        
        # Convert to LangChain messages
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            else:
                lc_messages.append(HumanMessage(content=msg["content"]))
        
        # Generate response
        response = await self.langchain_model.agenerate([lc_messages])
        text_content = response.generations[0][0].text
        
        return MultimodalResponse(text=text_content)
    
    async def _stream_response(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Stream response tokens."""
        
        if self.provider == LLMProvider.ANTHROPIC_CLAUDE_VISION:
            async for chunk in self._stream_claude_response(messages):
                yield chunk
        elif self.provider == LLMProvider.OPENAI_GPT4_VISION:
            async for chunk in self._stream_gpt4_response(messages):
                yield chunk
        else:
            async for chunk in self._stream_text_response(messages):
                yield chunk
    
    async def _stream_claude_response(
        self,
        messages: List[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Stream Claude response."""
        
        system_msg = None
        user_messages = messages
        
        if messages and messages[0]["role"] == "system":
            system_msg = messages[0]["content"]
            user_messages = messages[1:]
        
        stream = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_msg,
            messages=user_messages,
            stream=True
        )
        
        async for event in stream:
            if event.type == "content_block_delta":
                yield event.delta.text
    
    async def _stream_gpt4_response(
        self,
        messages: List[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Stream GPT-4 response."""
        
        stream = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _stream_text_response(
        self,
        messages: List[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Stream text response using LangChain."""
        
        # Convert to LangChain messages
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            else:
                lc_messages.append(HumanMessage(content=msg["content"]))
        
        # Stream response
        async for chunk in self.langchain_model.astream(lc_messages):
            yield chunk.content
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text response."""
        
        # Look for JSON blocks
        import re
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from response")
        
        # Try to parse the entire response as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    def _extract_confidence_scores(self, text: str) -> Dict[str, float]:
        """Extract confidence scores from response."""
        
        scores = {}
        
        # Look for confidence patterns
        import re
        confidence_pattern = r'confidence[:\s]+(\d+(?:\.\d+)?)'
        matches = re.findall(confidence_pattern, text, re.IGNORECASE)
        
        if matches:
            scores["overall"] = float(matches[0])
        
        # Look for specific confidence scores
        specific_pattern = r'(\w+)\s+confidence[:\s]+(\d+(?:\.\d+)?)'
        specific_matches = re.findall(specific_pattern, text, re.IGNORECASE)
        
        for name, score in specific_matches:
            scores[name.lower()] = float(score)
        
        return scores
    
    def _extract_reasoning_trace(self, text: str) -> List[str]:
        """Extract reasoning steps from response."""
        
        trace = []
        
        # Look for numbered steps
        import re
        step_pattern = r'(?:^|\n)\s*(?:\d+\.|\-|\*)\s*(.+?)(?=\n\s*(?:\d+\.|\-|\*)|$)'
        matches = re.findall(step_pattern, text, re.MULTILINE | re.DOTALL)
        
        if matches:
            trace = [step.strip() for step in matches if step.strip()]
        
        return trace
    
    async def analyze_image(
        self,
        image: Union[Path, Image.Image, np.ndarray],
        prompt: str,
        detail_level: str = "high"
    ) -> MultimodalResponse:
        """Analyze a single image with a prompt."""
        
        message = MultimodalMessage(
            text=prompt,
            images=[image],
            metadata={"detail_level": detail_level}
        )
        
        return await self.generate([message])
    
    async def compare_images(
        self,
        images: List[Union[Path, Image.Image, np.ndarray]],
        comparison_prompt: str
    ) -> MultimodalResponse:
        """Compare multiple images."""
        
        prompt = f"{comparison_prompt}\n\nPlease analyze and compare these {len(images)} images:"
        
        message = MultimodalMessage(
            text=prompt,
            images=images
        )
        
        return await self.generate([message])
    
    async def generate_from_description(
        self,
        description: str,
        style_hints: Optional[List[str]] = None,
        reference_images: Optional[List[Union[Path, Image.Image]]] = None
    ) -> MultimodalResponse:
        """Generate content from description with optional references."""
        
        prompt_parts = [description]
        
        if style_hints:
            prompt_parts.append(f"\nStyle hints: {', '.join(style_hints)}")
        
        if reference_images:
            prompt_parts.append(f"\nPlease consider the {len(reference_images)} reference images provided.")
        
        message = MultimodalMessage(
            text="\n".join(prompt_parts),
            images=reference_images or []
        )
        
        return await self.generate([message])


class VisionProcessor:
    """Process images for multimodal LLMs."""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        self.max_dimension = 2048
    
    async def process_image(
        self,
        image: Union[Path, Image.Image, np.ndarray]
    ) -> Dict[str, Any]:
        """Process image and return base64 encoded data."""
        
        # Convert to PIL Image
        if isinstance(image, Path):
            pil_image = Image.open(image)
        elif isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Resize if needed
        pil_image = self._resize_image(pil_image)
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        
        # Determine format
        format = "PNG" if pil_image.mode in ["RGBA", "P"] else "JPEG"
        media_type = f"image/{format.lower()}"
        
        pil_image.save(buffer, format=format)
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            "base64": base64_data,
            "media_type": media_type,
            "width": pil_image.width,
            "height": pil_image.height
        }
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image if it exceeds maximum dimensions."""
        
        if image.width <= self.max_dimension and image.height <= self.max_dimension:
            return image
        
        # Calculate new dimensions
        ratio = min(self.max_dimension / image.width, self.max_dimension / image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


class AudioProcessor:
    """Process audio for multimodal LLMs."""
    
    def __init__(self):
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.ogg'}
    
    async def transcribe(
        self,
        audio: Union[Path, bytes]
    ) -> str:
        """Transcribe audio to text."""
        
        # This would use a service like OpenAI Whisper
        # For now, return placeholder
        return "[Audio content would be transcribed here]"
    
    async def process_audio(
        self,
        audio: Union[Path, bytes]
    ) -> Dict[str, Any]:
        """Process audio and return metadata."""
        
        return {
            "transcript": await self.transcribe(audio),
            "duration": 0,  # Would calculate actual duration
            "format": "unknown"
        }
