import { api } from "@/utils/axios";

export interface IDeployResponse {
    success: boolean;
    message: string;
    contractAddress: string;
    network: string;
    contractName: string;
    explorerUrl: string;
}

export async function deploySmartContract(code: string) {
    try {
        let payload = {
            code: code,
            network: "primordial"
        }
        let res = await api.post("/deploy", payload)
        return res.data
    } catch (e: any) {
        console.log(e)
        throw (e)
    }
}

export async function saveDeployment(deployment: IDeployResponse, user_id: string) {
    try{
        let payload = {
            user_id: user_id,
            deployment: deployment
        }
        await api.post('/save_deployment', payload)
    }catch(e: any){
        console.log(e)
    }
}

export async function getDeployments(user_id: string) {
    try{
        let res = await api.get(`/get_deployments/${user_id}`)
        return res.data.deployments
    }catch(e: any){
        console.log(e)
    }
}