"use client";

import { useState, useEffect, useRef } from 'react';

interface TextChunkViewerProps {
  extractedText: string;
  selectedChunk?: {
    chunk_text: string;
    start_char: number;
    end_char: number;
    chunk_id: string;
  };
}

export default function TextChunkViewer({ extractedText, selectedChunk }: TextChunkViewerProps) {
  const [highlightedText, setHighlightedText] = useState<string>('');
  const textContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!selectedChunk || !extractedText) {
      setHighlightedText(extractedText);
      return;
    }

    const { start_char, end_char } = selectedChunk;
    
    // Create highlighted HTML
    const beforeText = extractedText.substring(0, start_char);
    const highlightText = extractedText.substring(start_char, end_char);
    const afterText = extractedText.substring(end_char);
    
    const highlightedHTML = `
      <div style="font-family: 'Courier New', monospace; white-space: pre-wrap; line-height: 1.6; padding: 16px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;">
        ${beforeText}<span id="highlighted-chunk" style="background-color: #fff3b0; padding: 2px 4px; border-radius: 3px; border: 1px solid #fbbf24; font-weight: 500;">${highlightText}</span>${afterText}
      </div>
    `;
    
    setHighlightedText(highlightedHTML);
    
    // Scroll to the highlighted chunk after a short delay to ensure DOM is updated
    setTimeout(() => {
      const highlightedElement = document.getElementById('highlighted-chunk');
      if (highlightedElement && textContainerRef.current) {
        highlightedElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center',
          inline: 'nearest'
        });
      }
    }, 100);
  }, [extractedText, selectedChunk]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-gray-100 rounded-lg">
        <h4 className="font-medium text-gray-900">Text Viewer</h4>
        {selectedChunk && (
          <div className="text-sm text-gray-600">
            Chunk: {selectedChunk.chunk_id} • Characters: {selectedChunk.start_char}-{selectedChunk.end_char}
          </div>
        )}
      </div>

      {/* Text Display */}
      <div className="border border-gray-200 rounded-lg overflow-hidden bg-white min-h-[400px]">
        {highlightedText ? (
          <div 
            ref={textContainerRef}
            className="p-4 h-full overflow-auto"
            dangerouslySetInnerHTML={{ __html: highlightedText }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>No text available</p>
          </div>
        )}
      </div>

      {/* Selected Chunk Info */}
      {selectedChunk && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="font-medium text-yellow-800 mb-2">Selected Chunk: {selectedChunk.chunk_id}</h4>
          <div className="bg-white p-3 rounded border border-yellow-300 mb-2">
            <p className="text-sm text-gray-800 break-words whitespace-pre-wrap font-mono">
              {selectedChunk.chunk_text}
            </p>
          </div>
          <p className="text-xs text-yellow-600">
            Character Range: {selectedChunk.start_char}-{selectedChunk.end_char} 
            ({selectedChunk.end_char - selectedChunk.start_char} characters)
          </p>
        </div>
      )}
    </div>
  );
}