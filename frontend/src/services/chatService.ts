import { api } from "../utils/axios";

export async function sendChat(prompt: string) {
    try{
        let res = await api.post("/generate", {
            prompt: prompt
        })
        let processedData: CodeResponse = separateTextAndCode(res?.data?.contract?? "")
        return processedData
    }catch(e: any){
        console.log(e)
    }
}


export interface CodeResponse {
    text: any;
    code: any;
}

function separateTextAndCode(aiResponse: string): CodeResponse {
    // Find the first occurrence of a code block (```)
    const codeBlockStart = aiResponse.indexOf('```solidity\n');
    
    if (codeBlockStart === -1) {
      throw new Error('No code block found in the response');
    }
  
    // Extract the text before the code block
    const textBefore = aiResponse.substring(0, codeBlockStart).trim();
  
    // Find the end of the code block (```) 
    const codeBlockEnd = aiResponse.indexOf('```', codeBlockStart + '```solidity\n'.length);
    
    if (codeBlockEnd === -1) {
      throw new Error('No closing code block found');
    }
  
    // Extract the code (excluding the opening ```solidity and closing ```)
    const code = aiResponse.substring(
      codeBlockStart + '```solidity\n'.length,
      codeBlockEnd
    ).trim();

    // Extract the text after the code block
    const textAfter = aiResponse.substring(codeBlockEnd + 3).trim();

    // Combine the before and after text as explanation
    const text = [textBefore, textAfter].filter(Boolean).join('\n\n').trim();
  
    return { text, code };
  }


  // --- New methods for chat history ---

export async function saveChat(user_id: string, chat_history: any[]) {
  try {
      let payload = {
          user_id: user_id,
          chat_history: chat_history
      };
      await api.post('/save_chat_history', payload);
  } catch (e: any) {
      console.log(e);
  }
}

export async function getChat(user_id: string) {
  try {
      return await api.get(`/get_chat_history/${user_id}`);
  } catch (e: any) {
      console.log(e);
  }
}