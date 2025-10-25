// app/types.ts
export interface Msg {
  id?: string;
  sender: string;
  message: string;
  expiry?: number;
  timestamp?: number;
}
