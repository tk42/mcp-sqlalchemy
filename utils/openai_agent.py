import json
import re
import httpx
import asyncio


class OpenAIAgent:
    def __init__(
        self,
        llamacpp_url: str,
        system_prompt: str = 'You are a helpful assistant.',
        max_tool_invocations: int = 5
    ):
        self.llamacpp_url = f"{llamacpp_url}/v1/chat/completions"
        self.model_id = "llamacpp"
        self.system_prompt = system_prompt
        self.max_tokens = 16384
        self.temperature = 0.0
        
        # 初期化時にsystemメッセージを設定
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.tools = None
        self.response_output_tags = []

        self.max_tool_invocations = max_tool_invocations
        self.tool_invocation_count = 0

    def set_system_prompt(self, prompt: str):
        """Systemプロンプトを変更し、メッセージ履歴をリセットする"""
        self.system_prompt = prompt
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]

    async def invoke_with_prompt(self, prompt: str):
        """ユーザーからの新たなプロンプトに応答する"""
        self.messages.append({"role": "user", "content": prompt})
        return await self.invoke()

    async def get_response(self):
        # ChatCompletion 用のペイロード
        payload = {
            "model": self.model_id,  # 使用するモデル名
            "messages": self.messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        headers = {
            "Content-Type": "application/json"
        }

        # toolsが設定されている場合のみパラメータに追加
        if self.tools:
            tools = self.tools.get_tools()
            if tools:  # toolsが空でない場合のみ追加
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
        
        try:
            # POST リクエストを送信 with timeout and retries
            timeout = httpx.Timeout(30.0, connect=10.0)  # 30 seconds total, 10 seconds for connection
            async with httpx.AsyncClient(timeout=timeout) as client:
                for attempt in range(3):  # Try up to 3 times
                    try:
                        response = await client.post(self.llamacpp_url, headers=headers, json=payload)
                        response.raise_for_status()
                        response_json = response.json()
                        print("Debug - LLaMA API Response:", json.dumps(response_json, indent=2))
                        
                        if "error" in response_json:
                            raise Exception(f"LLaMA API Error: {response_json['error']}")
                            
                        return response_json
                    except httpx.TimeoutException as e:
                        if attempt == 2:  # Last attempt
                            print(f"LLaMA API timeout after 3 attempts: {str(e)}")
                            raise
                        print(f"Attempt {attempt + 1} timed out, retrying...")
                        await asyncio.sleep(1)  # Wait 1 second before retrying
                    except Exception as e:
                        if attempt == 2:  # Last attempt
                            raise
                        print(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
                        await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in LLaMA API call: {str(e)}")
            raise

    async def invoke(self):
        if self.tool_invocation_count > self.max_tool_invocations:
            # ツール呼び出し回数の上限に達したら終了
            return "Tool invocation limit exceeded. Stopping to prevent infinite loop."

        try:
            completion = await self.get_response()
            
            if "choices" not in completion or not completion["choices"]:
                print("Invalid response format from LLaMA API:", json.dumps(completion, indent=2))
                return "Error: Invalid response from LLaMA API"

            choice = completion["choices"][0]
            message = choice["message"]
            finish_reason = choice["finish_reason"]
            assistant_content = message["content"] if message.get("content") else ""

            # 必要ならレスポンスタグ処理
            if self.response_output_tags and len(self.response_output_tags) == 2:
                pattern = f"(?s).*{re.escape(self.response_output_tags[0])}(.*?){re.escape(self.response_output_tags[1])}"
                match = re.search(pattern, assistant_content)
                if match:
                    assistant_content = match.group(1)

            self.messages.append({
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": message.get("tool_calls") if isinstance(message, dict) else None
            })

            # ツール呼び出しがある場合
            if finish_reason == "tool_calls":
                self.tool_invocation_count += 1

                tool_calls = message.get("tool_calls", [])
                for call in tool_calls:
                    func_info = call["function"]
                    func_name = func_info["name"]
                    arguments_str = func_info["arguments"]
                    arguments = json.loads(arguments_str)
                    tool_use_id = call["id"]

                    # MCPサーバ上のツールを実行
                    tool_result = await self.tools.execute_tool(func_name, arguments)
                    # ツール結果をtoolロールメッセージとして履歴にコミット
                    function_call_result_message = {
                        "role": "tool",
                        "content": json.dumps(tool_result),
                        "tool_call_id": tool_use_id
                    }
                    self.messages.append(function_call_result_message)

                # ツール使用結果を反映させるため再度モデルに問い合わせ
                return await self.invoke()

            return assistant_content if assistant_content else ""
        except Exception as e:
            print(f"Error in invoke: {str(e)}")
            raise

# import asyncio
# from typing import Optional

# async def main():
#     # OpenAIAgentのインスタンス作成
#     agent = OpenAIAgent(
#         model_id="gpt-4o",  # モデルIDを指定
#         system_prompt="You are a helpful assistant that provides clear and concise answers."
#     )
    
#     try:
#         # テスト用のプロンプト
#         test_prompt = "Please choose three expensive products."
        
#         # エージェントを呼び出し
#         response = await agent.invoke_with_prompt(test_prompt)
#         print(f"Response: {response}")
        
#     except Exception as e:
#         print(f"Error occurred: {e}")

# if __name__ == "__main__":
#     # asyncio.run()を使用してメインの非同期関数を実行
#     asyncio.run(main())