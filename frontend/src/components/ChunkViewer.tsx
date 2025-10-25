"use client";

import { useState, useEffect } from 'react';
import FileManager from './FileManager';
import MethodSelector from './MethodSelector';
import ParameterControls from './ParameterControls';
import ChunkView from './ChunkView';
import { ChunkingMethod, ChunkingParameters, ChunkResult } from '@/types/chunking';

const API_BASE_URL = 'http://localhost:8000';

export default function ChunkViewer() {
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<string>('llamaindex');
  const [parameters, setParameters] = useState<Record<string, ChunkingParameters>>({});
  const [chunkResults, setChunkResults] = useState<ChunkResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableMethods, setAvailableMethods] = useState<Record<string, ChunkingMethod>>({});
  const [hasUnprocessedChanges, setHasUnprocessedChanges] = useState(false);

  // Load available methods on component mount
  useEffect(() => {
    console.log('ChunkViewer component mounted, loading methods...');
    loadAvailableMethods();
  }, []);

  const loadAvailableMethods = async () => {
    try {
      console.log('Loading available methods from:', `${API_BASE_URL}/chunk/methods`);
      const response = await fetch(`${API_BASE_URL}/chunk/methods`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      console.log('Response headers:', response.headers);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Received data:', data);
      console.log('Data type:', typeof data);
      console.log('Data methods:', data.methods);
      console.log('Setting available methods:', data.methods);
      setAvailableMethods(data.methods);
      console.log('Available methods set, current state:', data.methods);
      
      // Initialize default parameters for each method
      const defaultParams: Record<string, ChunkingParameters> = {};
      Object.keys(data.methods).forEach(method => {
        const methodInfo = data.methods[method];
        const defaultParamValues: ChunkingParameters = {};
        Object.keys(methodInfo.parameters).forEach(param => {
          defaultParamValues[param] = methodInfo.parameters[param].default;
        });
        defaultParams[method] = defaultParamValues;
      });
      console.log('Setting parameters:', defaultParams);
      setParameters(defaultParams);
      console.log('Successfully loaded methods and parameters');
    } catch (err) {
      console.error('Error loading available methods:', err);
      console.error('Error details:', err);
      setError(`Failed to load available methods: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleFileUpload = (filePath: string) => {
    setUploadedFile(filePath);
    setChunkResults([]);
    setError(null);
    setHasUnprocessedChanges(false);
  };

  const handleCompareChunks = async () => {
    if (!uploadedFile || !selectedMethod) {
      setError('Please upload a file and select a method');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const requestBody = {
        file_path: uploadedFile,
        methods: [selectedMethod],
        parameters: parameters
      };

      console.log('Frontend request body:', requestBody);
      console.log('API URL:', `${API_BASE_URL}/chunk/compare`);

      const response = await fetch(`${API_BASE_URL}/chunk/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Success response:', data);
      setChunkResults(data.comparisons);
      setHasUnprocessedChanges(false);
    } catch (err) {
      console.error('Frontend error:', err);
      setError(err instanceof Error ? err.message : 'Failed to compare chunks');
    } finally {
      setLoading(false);
    }
  };

  const handleMethodChange = (method: string) => {
    setSelectedMethod(method);
    // Clear results when method changes
    setChunkResults([]);
    setHasUnprocessedChanges(true);
  };

  const handleParameterChange = (method: string, newParameters: ChunkingParameters) => {
    setParameters(prev => ({
      ...prev,
      [method]: newParameters
    }));
    // Clear results when parameters change
    setChunkResults([]);
    setHasUnprocessedChanges(true);
  };

  return (
    <div className="space-y-6">
      {/* File Management Section */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">1. Select Document</h2>
        <p className="text-sm text-gray-600 mb-4">
          Upload a new file or select from previously uploaded files.
        </p>
        <FileManager 
          onFileSelect={handleFileUpload} 
          selectedFile={uploadedFile}
        />
      </div>

      {/* Method Selection */}
      {uploadedFile && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">2. Select Chunking Method</h2>
          <p className="text-sm text-gray-600 mb-4">
            Choose a chunking method for document processing and text highlighting.
          </p>
          <MethodSelector
            availableMethods={availableMethods}
            selectedMethod={selectedMethod}
            onMethodChange={handleMethodChange}
          />
        </div>
      )}

      {/* Parameter Controls */}
      {uploadedFile && selectedMethod && Object.keys(availableMethods).length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">3. Adjust Parameters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[selectedMethod].map(method => {
              const methodInfo = availableMethods[method];
              if (!methodInfo) {
                return (
                  <div key={method} className="space-y-4">
                    <div className="border-b border-gray-200 pb-2">
                      <h3 className="font-medium text-gray-900">Loading...</h3>
                      <p className="text-sm text-gray-600">Loading method information...</p>
                    </div>
                  </div>
                );
              }
              return (
                <ParameterControls
                  key={method}
                  method={method}
                  methodInfo={methodInfo}
                  parameters={parameters[method] || {}}
                  onParameterChange={(newParams) => handleParameterChange(method, newParams)}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Process Button */}
      {uploadedFile && selectedMethod && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">4. Process Document</h2>
          <div className="flex flex-col items-center space-y-3">
            {hasUnprocessedChanges && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-yellow-800 text-sm">
                  ⚠️ Parameters have been changed. Click the button below to process with new settings.
                </p>
              </div>
            )}
            <button
              onClick={handleCompareChunks}
              disabled={loading}
              className="btn-primary px-8 py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Process Document with Selected Method'}
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Results */}
      {chunkResults.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">5. View Results</h2>
          <ChunkView results={chunkResults} filePath={uploadedFile || undefined} />
        </div>
      )}
    </div>
  );
}
