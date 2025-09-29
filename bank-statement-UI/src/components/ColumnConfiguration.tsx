
import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ColumnDefinition } from '../store';

interface ColumnConfigurationProps {
  columns: ColumnDefinition[];
  onChange: (columns: ColumnDefinition[]) => void;
}

export function ColumnConfiguration({ columns, onChange }: ColumnConfigurationProps) {
  const [newColumnName, setNewColumnName] = useState('');

  const addColumn = () => {
    if (!newColumnName.trim()) return;
    
    const newColumn: ColumnDefinition = {
      id: crypto.randomUUID(),
      name: newColumnName.trim(),
    };
    
    onChange([...columns, newColumn]);
    setNewColumnName('');
  };

  const removeColumn = (id: string) => {
    onChange(columns.filter(column => column.id !== id));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addColumn();
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl">Configure Extraction Columns</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-500 mb-4">
          Add the columns you want to extract from your bank statement
        </p>
        
        <div className="flex gap-2 mb-6">
          <div className="flex-grow">
            <Input
              value={newColumnName}
              onChange={(e) => setNewColumnName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter column name (e.g., Date, Description, Amount)"
              className="w-full"
            />
          </div>
          <Button onClick={addColumn} disabled={!newColumnName.trim()}>
            <Plus className="h-4 w-4 mr-2" />
            Add
          </Button>
        </div>

        {columns.length === 0 ? (
          <div className="py-8 text-center text-gray-500 bg-muted/30 rounded-lg">
            <p>No columns added yet</p>
            <p className="text-sm mt-1">Add columns to extract from your bank statement</p>
          </div>
        ) : (
          <div className="space-y-2">
            {columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
              >
                <span className="font-medium">{column.name}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeColumn(column.id)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
