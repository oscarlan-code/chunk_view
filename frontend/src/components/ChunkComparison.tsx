"use client";

import { useState } from 'react';
import { ChunkResult } from '@/types/chunking';
import TextChunkViewer from './TextChunkViewer';

interface ChunkViewProps {
  results: ChunkResult[];
  filePath?: string;
}

export default function ChunkView({ results, filePath }: ChunkViewProps) {
  const [selectedMethod, setSelectedMethod] = useState<string | null>(
    results.length > 0 ? results[0].method : null
  );
  const [selectedChunk, setSelectedChunk] = useState<number | null>(null);

  const selectedResult = results.find(r => r.method === selectedMethod);

  const getMethodColor = (method: string) => {
    const colors = {
      llamaindex: 'bg-blue-100 text-blue-800 border-blue-200',
      langchain: 'bg-green-100 text-green-800 border-green-200'
    };
    return colors[method as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="w-full">
      {/* Method Selector */}
      <div className="mb-4">
        <div className="flex space-x-2">
          {results.map((result) => (
            <button
              key={result.method}
              onClick={() => setSelectedMethod(result.method)}
              className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
                selectedMethod === result.method
                  ? 'bg-blue-100 text-blue-800 border-blue-300'
                  : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
              }`}
            >
              {result.method}
            </button>
          ))}
        </div>
      </div>

      {/* Statistics */}
      {selectedResult && (
        <div className="mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {selectedResult.total_chunks}
              </div>
              <div className="text-sm text-gray-600">Total Chunks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(selectedResult.chunks.reduce((acc, chunk) => acc + chunk.char_count, 0) / selectedResult.total_chunks)}
              </div>
              <div className="text-sm text-gray-600">Avg Chars</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(selectedResult.chunks.reduce((acc, chunk) => acc + chunk.word_count, 0) / selectedResult.total_chunks)}
              </div>
              <div className="text-sm text-gray-600">Avg Words</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {selectedResult.processing_time.toFixed(2)}s
              </div>
              <div className="text-sm text-gray-600">Processing Time</div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Side by Side Layout */}
      <div className="flex gap-4 h-[700px]">
        {/* Left Side - Chunk List */}
        <div className="w-1/2 min-w-0">
          <div className="bg-white border border-gray-200 rounded-lg h-full flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h4 className="font-medium text-gray-900">Chunks</h4>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {selectedResult && (
                <div className="space-y-2">
                  {selectedResult.chunks.map((chunk, index) => (
                    <div
                      key={chunk.chunk_id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedChunk === index
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedChunk(selectedChunk === index ? null : index)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-900">
                            Chunk {chunk.chunk_index + 1}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getMethodColor(selectedResult.method)}`}>
                            {selectedResult.method}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {chunk.char_count} chars, {chunk.word_count} words
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-700 line-clamp-3">
                        {chunk.chunk_text.length > 120 
                          ? `${chunk.chunk_text.substring(0, 120)}...` 
                          : chunk.chunk_text
                        }
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side - Viewer */}
        {filePath && selectedResult && (
          <div className="w-1/2 min-w-0">
            <div className="bg-white border border-gray-200 rounded-lg h-full flex flex-col">
              <div className="p-4 border-b border-gray-200">
                <h4 className="font-medium text-gray-900">Text Viewer</h4>
                <p className="text-sm text-gray-600 mt-1">Highlighting based on extracted text for maximum accuracy</p>
              </div>
              <div className="flex-1 overflow-hidden">
                <TextChunkViewer
                  extractedText={selectedResult.metadata?.extracted_text || ''}
                  selectedChunk={selectedChunk !== null && 
                    selectedResult.chunks[selectedChunk].start_char !== undefined && 
                    selectedResult.chunks[selectedChunk].end_char !== undefined ? {
                    chunk_text: selectedResult.chunks[selectedChunk].chunk_text,
                    start_char: selectedResult.chunks[selectedChunk].start_char!,
                    end_char: selectedResult.chunks[selectedChunk].end_char!,
                    chunk_id: selectedResult.chunks[selectedChunk].chunk_id
                  } : undefined}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Method Comparison */}
      {results.length > 1 && (
        <div className="mt-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Method Comparison</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.map((result) => (
                <div key={result.method} className="p-3 bg-white rounded-lg border">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getMethodColor(result.method)}`}>
                      {result.method}
                    </span>
                    <span className="text-xs text-gray-500">
                      {result.processing_time.toFixed(2)}s
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <div>Chunks: {result.total_chunks}</div>
                    <div>Avg Length: {Math.round(result.chunks.reduce((acc, chunk) => acc + chunk.char_count, 0) / result.total_chunks)} chars</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
