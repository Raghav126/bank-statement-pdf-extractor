
import { atom } from 'jotai';

export type ColumnDefinition = {
  id: string;
  name: string;
  description?: string;
  isRequired?: boolean;
};

export type Transaction = {
  id: string;
  [key: string]: string | number | Date;
};

// Store the uploaded file
export const fileAtom = atom<File | null>(null);

// Store the column definitions specified by the user
export const columnsAtom = atom<ColumnDefinition[]>([]);

// Store the extracted transactions
export const transactionsAtom = atom<Transaction[]>([]);

// Store the loading state
export const isLoadingAtom = atom<boolean>(false);

// Store any errors
export const errorAtom = atom<string | null>(null);
