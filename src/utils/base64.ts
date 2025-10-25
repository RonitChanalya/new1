// src/utils/base64.ts
import { fromByteArray, toByteArray } from 'base64-js';

export const bytesToBase64 = (u8: Uint8Array) => fromByteArray(u8);
export const base64ToBytes = (b64: string) => toByteArray(b64);
