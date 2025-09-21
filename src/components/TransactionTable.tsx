
import React from 'react';
import { Download } from 'lucide-react';
import { CSVLink } from 'react-csv';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from './ui/table';
import { Transaction } from '../store';

interface TransactionTableProps {
  transactions: Transaction[];
  columns: string[];
  isLoading?: boolean;
}

export function TransactionTable({ transactions, columns, isLoading = false }: TransactionTableProps) {
  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-xl">Extracted Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-60 flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
              <p className="mt-2 text-gray-500">Extracting transactions...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (transactions.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-xl">Extracted Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-12 text-center text-gray-500">
            <p>No transactions have been extracted yet</p>
            <p className="text-sm mt-1">Upload a statement and configure columns to extract transactions</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const csvData = transactions.map(transaction => {
    const row: Record<string, string | number | Date> = {};
    columns.forEach(column => {
      row[column] = transaction[column] || '';
    });
    return row;
  });

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-xl">Extracted Transactions</CardTitle>
        <CSVLink
          data={csvData}
          filename="bank_transactions.csv"
          className="no-underline"
        >
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
            Download CSV
          </Button>
        </CSVLink>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead key={column}>{column}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((transaction, index) => (
                <TableRow key={transaction.id || index}>
                  {columns.map((column) => (
                    <TableCell key={`${transaction.id || index}-${column}`}>
                      {transaction[column] !== undefined ? String(transaction[column]) : ''}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
