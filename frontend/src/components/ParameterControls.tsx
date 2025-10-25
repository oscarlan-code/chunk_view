"use client";

import { useState, useEffect } from 'react';
import { ChunkingMethod, ChunkingParameters } from '@/types/chunking';

interface ParameterControlsProps {
  method: string;
  methodInfo: ChunkingMethod | undefined;
  parameters: ChunkingParameters;
  onParameterChange: (parameters: ChunkingParameters) => void;
}

export default function ParameterControls({
  method,
  methodInfo,
  parameters,
  onParameterChange
}: ParameterControlsProps) {
  const [localParameters, setLocalParameters] = useState<ChunkingParameters>(parameters);

  useEffect(() => {
    setLocalParameters(parameters);
  }, [parameters]);

  // Early return if methodInfo is not available
  if (!methodInfo) {
    return (
      <div className="space-y-4">
        <div className="border-b border-gray-200 pb-2">
          <h3 className="font-medium text-gray-900">Loading...</h3>
          <p className="text-sm text-gray-600">Loading method information...</p>
        </div>
      </div>
    );
  }

  const handleParameterChange = (paramName: string, value: any) => {
    const newParameters = { ...localParameters, [paramName]: value };
    setLocalParameters(newParameters);
    onParameterChange(newParameters);
  };

  const renderParameterInput = (paramName: string, paramInfo: any) => {
    const value = localParameters[paramName] ?? paramInfo.default;

    switch (paramInfo.type) {
      case 'int':
      case 'float':
        return (
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {paramName}
            </label>
            <input
              type="number"
              min={paramInfo.min}
              max={paramInfo.max}
              step={paramInfo.type === 'float' ? 0.1 : 1}
              value={value}
              onChange={(e) => handleParameterChange(paramName, paramInfo.type === 'float' ? parseFloat(e.target.value) : parseInt(e.target.value))}
              className="input-field"
            />
          </div>
        );
      case 'bool':
        return (
          <div className="flex items-center h-5">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleParameterChange(paramName, e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor={paramName} className="ml-2 text-sm text-gray-900">
              {paramName}
            </label>
          </div>
        );
      case 'list':
        return (
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {paramName}
            </label>
            <input
              type="text"
              value={Array.isArray(value) ? value.join(', ') : value}
              onChange={(e) => handleParameterChange(paramName, e.target.value.split(',').map((s: string) => s.trim()))}
              className="input-field"
            />
          </div>
        );
      default:
        return (
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {paramName}
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => handleParameterChange(paramName, e.target.value)}
              className="input-field"
            />
          </div>
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="border-b border-gray-200 pb-2">
        <h3 className="font-medium text-gray-900">{methodInfo.name}</h3>
        <p className="text-sm text-gray-600">{methodInfo.description}</p>
      </div>
      
      <div className="space-y-4">
        {Object.entries(methodInfo.parameters).map(([paramName, paramInfo]) => (
          <div key={paramName}>
            {renderParameterInput(paramName, paramInfo)}
          </div>
        ))}
      </div>
    </div>
  );
}