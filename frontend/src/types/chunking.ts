export interface ChunkingMethod {
  name: string;
  description: string;
  parameters: Record<string, {
    type: string;
    default: any;
    min?: number;
    max?: number;
  }>;
}

export interface ChunkingParameters {
  [key: string]: any;
}

export interface Chunk {
  chunk_id: string;
  chunk_index: number;
  chunk_text: string;
  char_count: number;
  word_count: number;
  start_char?: number;
  end_char?: number;
  coordinates?: {
    bbox: number[];
    page: number;
  };
}

export interface ChunkResult {
  method: string;
  parameters: ChunkingParameters;
  chunks: Chunk[];
  total_chunks: number;
  processing_time: number;
  metadata?: {
    extracted_text?: string;
    [key: string]: any;
  };
}
