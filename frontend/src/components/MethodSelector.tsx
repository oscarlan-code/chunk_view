"use client";

import { ChunkingMethod } from '@/types/chunking';

interface MethodSelectorProps {
  availableMethods: Record<string, ChunkingMethod>;
  selectedMethod: string;
  onMethodChange: (method: string) => void;
}

export default function MethodSelector({ 
  availableMethods, 
  selectedMethod, 
  onMethodChange 
}: MethodSelectorProps) {
  console.log('MethodSelector received availableMethods:', availableMethods);
  console.log('MethodSelector received selectedMethod:', selectedMethod);
  
  const handleMethodChange = (method: string) => {
    onMethodChange(method);
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        Select a chunking method:
      </p>
      
      <div className="max-w-md">
        <select
          value={selectedMethod}
          onChange={(e) => handleMethodChange(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
        >
          {Object.entries(availableMethods).map(([methodKey, methodInfo]) => (
            <option key={methodKey} value={methodKey}>
              {methodInfo.name}
            </option>
          ))}
        </select>
      </div>

      {/* Show selected method details */}
      {selectedMethod && availableMethods[selectedMethod] && (
        <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="font-medium text-gray-900">
              {availableMethods[selectedMethod].name}
            </h3>
          </div>
          <p className="text-sm text-gray-600 mb-3">
            {availableMethods[selectedMethod].description}
          </p>
          <div className="flex flex-wrap gap-1">
            {Object.keys(availableMethods[selectedMethod].parameters).map(param => (
              <span
                key={param}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700"
              >
                {param}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
