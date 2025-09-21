
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from '../lib/axios';
import { ColumnDefinition, Transaction } from '../store';

// Upload a PDF and extract transactions
export const useExtractTransactions = () => {
  return useMutation({
    mutationFn: async ({ 
      file, 
      columns 
    }: { 
      file: File; 
      columns: ColumnDefinition[] 
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('columns', JSON.stringify(columns));
      
      const { data } = await axios.post<{ transactions: Transaction[] }>(
        '/process-bank-statement-json',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      return data.transactions;
    }
  });
};
