
const hre = require("hardhat");

async function main() {
    const TestToken = await hre.ethers.getContractFactory("TestToken");
    const contract = await TestToken.deploy();
    await contract.waitForDeployment();
    
    const address = await contract.getAddress();
    console.log("TestToken deployed to:", address);
    
    // Return deployment info as JSON
    console.log(JSON.stringify({
        success: true,
        contractAddress: address,
        network: "primordial",
        contractName: "TestToken"
    }));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }));
        process.exit(1);
    });
