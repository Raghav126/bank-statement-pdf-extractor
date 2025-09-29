
import React, { useState, useCallback, memo } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileIcon, Maximize2, Minimize2, X } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

interface FileUploadProps {
  onFileChange?: (file: File | null) => void;
  onToggleView?: () => void;
  isExpanded?: boolean;
}

export const FileUpload = memo(function FileUpload({ 
  onFileChange, 
  onToggleView, 
  isExpanded = false 
}: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelected = useCallback(
    (selectedFile: File) => {
      if (selectedFile.type !== 'application/pdf') {
        setError('Please upload a PDF file');
        return;
      }
      setFile(selectedFile);
      if (onFileChange) {
        onFileChange(selectedFile);
      }
      setError(null);
    },
    [onFileChange]
  );

  const removeFile = useCallback(() => {
    setFile(null);
    if (onFileChange) {
      onFileChange(null);
    }
  }, [onFileChange]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        handleFileSelected(acceptedFiles[0]);
      }
    },
    [handleFileSelected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
  });

  // When in expanded view, display a more compact version of the component
  if (isExpanded && file) {
    return (
      <Card className="w-full animate-fade-in">
        <CardContent className="pt-4 pb-4">
          <div className="flex items-center justify-between bg-muted/50 rounded-lg p-3">
            <div className="flex items-center space-x-3">
              <FileIcon className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm font-medium truncate max-w-[200px] sm:max-w-xs md:max-w-md">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={onToggleView}
                title="Exit preview"
                className="transition-all hover:bg-red-100 hover:text-red-600 hover:border-red-300 duration-200"
              >
                <X size={16} className="mr-1" />
                <span className="hidden sm:inline">Exit Preview</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardContent className="pt-6">
        {error && (
          <div className="mb-4 p-3 text-sm text-red-500 bg-red-50 rounded-md animate-fade-in">
            {error}
          </div>
        )}
        
        {!file ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-300 ${
              isDragActive
                ? 'border-primary bg-primary/5 scale-105'
                : 'border-gray-300 hover:border-primary/50 hover:bg-primary/5'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="h-10 w-10 mx-auto text-gray-400 mb-4 transition-transform group-hover:scale-110" />
            <p className="text-sm text-gray-500 mb-1">
              {isDragActive
                ? 'Drop the PDF here'
                : 'Drag and drop a bank statement PDF, or click to browse'}
            </p>
            <p className="text-xs text-gray-400">Only PDF files are supported</p>
          </div>
        ) : (
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg animate-fade-in transition-all duration-300">
            <div className="flex items-center space-x-3">
              <FileIcon className="h-8 w-8 text-primary" />
              <div>
                <p className="text-sm font-medium truncate max-w-[200px] sm:max-w-xs md:max-w-md">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <div className="flex space-x-2">
              {file && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={onToggleView}
                  title={isExpanded ? "Collapse view" : "Expand view"}
                  className="transition-all duration-200 hover:bg-primary/10"
                >
                  {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                </Button>
              )}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={removeFile}
                className="transition-all duration-200 hover:bg-red-100 hover:text-red-600 hover:border-red-300"
              >
                Change
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

