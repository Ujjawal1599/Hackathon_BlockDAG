import React from "react";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
} from "@/components/ui/drawer";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";

interface Deployment {
  contractName?: string;
  contractAddress?: string;
  network?: string;
  timestamp?: string;
  explorerUrl?: string;
  [key: string]: any;
}

interface DeploymentHistoryTableProps {
  deployments: Deployment[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DeploymentHistoryTable: React.FC<DeploymentHistoryTableProps> = ({ deployments, open, onOpenChange }) => (
  <Drawer open={open} onOpenChange={onOpenChange} direction="right">
    <DrawerContent className="w-1/2 h-full ml-auto">
      <DrawerHeader>
        <DrawerTitle>Deployment History</DrawerTitle>
        <DrawerDescription>All your contract deployments</DrawerDescription>
        {/* <button
          className="absolute top-2 right-2 text-gray-400 hover:text-white text-2xl"
          onClick={() => onOpenChange(false)}
          aria-label="Close"
        >
          &times;
        </button> */}
      </DrawerHeader>
      <div className="overflow-x-auto px-4 pb-4 mt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Contract Name</TableHead>
              <TableHead>Address</TableHead>
              <TableHead>Network</TableHead>
              <TableHead>Timestamp</TableHead>
              <TableHead>Explorer</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {deployments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-4">No deployments found.</TableCell>
              </TableRow>
            ) : (
              deployments.map((d, idx) => (
                <TableRow key={idx}>
                  <TableCell>{d.contractName || '-'}</TableCell>
                  <TableCell className="break-all">{d.contractAddress || '-'}</TableCell>
                  <TableCell>{d.network || '-'}</TableCell>
                  <TableCell>{d.timestamp ? new Date(d.timestamp).toLocaleString() : '-'}</TableCell>
                  <TableCell>
                    {d.explorerUrl ? (
                      <a href={d.explorerUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">Explorer</a>
                    ) : '-'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </DrawerContent>
  </Drawer>
);

export default DeploymentHistoryTable; 