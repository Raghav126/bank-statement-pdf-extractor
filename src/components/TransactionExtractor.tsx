
import React, { useState, useCallback, useRef } from 'react';
import { useAtom } from 'jotai';
import { columnsAtom, transactionsAtom, isLoadingAtom, ColumnDefinition, Transaction } from '../store';
import { FileUpload } from './FileUpload';
import { ColumnConfiguration } from './ColumnConfiguration';
import { TransactionTable } from './TransactionTable';
import { Button } from './ui/button';
import { Container } from './ui/container';
import { useExtractTransactions } from '../api/useTransactionExtraction';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from './ui/resizable';

export function TransactionExtractor() {
  const [file, setFile] = useState<File | null>(null);
  const [columns, setColumns] = useAtom(columnsAtom);
  const [transactions, setTransactions] = useAtom(transactionsAtom);
  const [isLoading, setIsLoading] = useAtom(isLoadingAtom);
  const [isExpanded, setIsExpanded] = useState(false);
  const pdfUrl = useRef<string | null>(null);
  
  const mutation = useExtractTransactions();
  
  const extractTransactions = useCallback(async () => {
  if (!file || columns.length === 0) return;

  try {
    setIsLoading(true);

    // Call the API
    const extractedTransactions = await mutation.mutateAsync({ file, columns });
    console.log("Extracted Transactions:", extractedTransactions);
    setTransactions(extractedTransactions);
  } catch (error) {
    console.error("Error extracting transactions:", error);
  } finally {
    setIsLoading(false);
  }
}, [file, columns, setTransactions, setIsLoading, mutation]);
  
  const columnNames = columns.map(col => col.name);

  const handleFileChange = useCallback((newFile: File | null) => {
    setFile(newFile);
    if (newFile) {
      // Create URL for the pdf
      if (pdfUrl.current) URL.revokeObjectURL(pdfUrl.current);
      pdfUrl.current = URL.createObjectURL(newFile);
    } else {
      if (pdfUrl.current) {
        URL.revokeObjectURL(pdfUrl.current);
        pdfUrl.current = null;
      }
      setIsExpanded(false);
    }
  }, []);

  const toggleExpandedView = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  const renderConfigSection = () => (
    <div className="grid gap-8">
      <ColumnConfiguration columns={columns} onChange={setColumns} />
      
      <div className="flex justify-center">
        <Button 
          size="lg"
          disabled={!file || columns.length === 0 || isLoading}
          onClick={extractTransactions}
          className="px-8 transition-all hover:scale-105 duration-200"
        >
          Extract Transactions
        </Button>
      </div>
      
      <TransactionTable 
        transactions={transactions} 
        columns={columnNames}
        isLoading={isLoading} 
      />
    </div>
  );

  if (isExpanded && file && pdfUrl.current) {
    return (
      <div className="min-h-screen bg-background py-12 animate-fade-in">
        <Container>
          <div className="mb-6 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">
              Bank Statement Transaction Extractor
            </h1>
            <p className="text-gray-500 max-w-md mx-auto">
              Upload your bank statement, configure the columns, and extract your transactions
            </p>
          </div>
          
          <div className="mb-4 w-full">
            <FileUpload 
              onFileChange={handleFileChange} 
              onToggleView={toggleExpandedView}
              isExpanded={isExpanded}
            />
          </div>
          
          <ResizablePanelGroup 
            direction="horizontal" 
            className="min-h-[600px] rounded-lg border animate-scale-in transition-all duration-300"
          >
            <ResizablePanel defaultSize={40} minSize={20}>
              <div className="h-full p-4 overflow-hidden flex flex-col">
                <h3 className="text-lg font-semibold mb-4">PDF Preview</h3>
                <iframe 
                  src={pdfUrl.current} 
                  className="w-full flex-grow rounded-md border animate-fade-in"
                  title="PDF Preview"
                />
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle className="transition-opacity hover:opacity-100 opacity-70" />
            <ResizablePanel defaultSize={60} minSize={30}>
              <div className="h-full p-4 overflow-auto animate-fade-in">
                {renderConfigSection()}
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </Container>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12">
      <Container>
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">
            Bank Statement Transaction Extractor
          </h1>
          <p className="text-gray-500 max-w-md mx-auto">
            Upload your bank statement, configure the columns, and extract your transactions
          </p>
        </div>
        
        <div className="grid gap-8">
          <FileUpload 
            onFileChange={handleFileChange} 
            onToggleView={file ? toggleExpandedView : undefined}
            isExpanded={isExpanded}
          />
          
          {renderConfigSection()}
        </div>
      </Container>
    </div>
  );
}
