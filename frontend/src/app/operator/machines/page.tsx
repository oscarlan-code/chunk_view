'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, MessageSquare, FileText, AlertCircle, CheckCircle, Clock } from 'lucide-react';

interface Machine {
  id: number;
  name: string;
  production_line: string;
  factory: string;
  status: string;
  last_maintenance: string | null;
  document_count: number;
  has_processed_documents: boolean;
  processing_status: 'ready' | 'processing' | 'no_documents' | 'failed';
}

interface QueryResponse {
  response: string;
  source: string;
  machine_id: number;
  documents_available: number;
  confidence_score: number | null;
  source_documents: string[] | null;
  processing_time: number | null;
}

export default function MachineDashboard() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null);
  const [showQueryModal, setShowQueryModal] = useState(false);
  const [query, setQuery] = useState('');
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);

  useEffect(() => {
    fetchMachines();
  }, []);

  const fetchMachines = async () => {
    try {
      const response = await fetch('http://localhost:8000/machines/dashboard');
      if (response.ok) {
        const data = await response.json();
        setMachines(data);
      } else {
        console.error('Failed to fetch machines');
      }
    } catch (error) {
      console.error('Error fetching machines:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    if (!selectedMachine || !query.trim()) return;

    setQueryLoading(true);
    try {
      const response = await fetch('http://localhost:8000/query/machine', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          machine_id: selectedMachine.id,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setQueryResponse(data);
      } else {
        console.error('Failed to get query response');
      }
    } catch (error) {
      console.error('Error querying machine:', error);
    } finally {
      setQueryLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'working':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'maintenance':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'down':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getProcessingStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <Badge className="bg-green-100 text-green-800">Ready</Badge>;
      case 'processing':
        return <Badge className="bg-yellow-100 text-yellow-800">Processing</Badge>;
      case 'no_documents':
        return <Badge className="bg-gray-100 text-gray-800">No Documents</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  const openQueryModal = (machine: Machine) => {
    setSelectedMachine(machine);
    setShowQueryModal(true);
    setQuery('');
    setQueryResponse(null);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Machine Dashboard</h1>
        <p className="text-gray-600 mt-2">Query machine-specific documentation and get intelligent responses</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {machines.map((machine) => (
          <Card key={machine.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{machine.name}</CardTitle>
                {getStatusIcon(machine.status)}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>{machine.production_line}</span>
                <span>•</span>
                <span>{machine.factory}</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Documents:</span>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium">{machine.document_count}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Status:</span>
                  {getProcessingStatusBadge(machine.processing_status)}
                </div>

                <Button
                  onClick={() => openQueryModal(machine)}
                  disabled={machine.processing_status === 'no_documents'}
                  className="w-full"
                  variant={machine.processing_status === 'ready' ? 'default' : 'secondary'}
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  {machine.processing_status === 'ready' ? 'Ask Question' : 'No Documents'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Query Modal */}
      {showQueryModal && selectedMachine && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Query: {selectedMachine.name}</h2>
              <Button
                onClick={() => setShowQueryModal(false)}
                variant="ghost"
                size="sm"
              >
                ✕
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Question
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about this machine..."
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              <Button
                onClick={handleQuery}
                disabled={!query.trim() || queryLoading}
                className="w-full"
              >
                {queryLoading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Processing...
                  </div>
                ) : (
                  <div className="flex items-center">
                    <Search className="h-4 w-4 mr-2" />
                    Ask Question
                  </div>
                )}
              </Button>

              {queryResponse && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">Response</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <span>Confidence: {queryResponse.confidence_score ? `${(queryResponse.confidence_score * 100).toFixed(1)}%` : 'N/A'}</span>
                      {queryResponse.processing_time && (
                        <span>• {queryResponse.processing_time.toFixed(2)}s</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-gray-700 mb-4">
                    {queryResponse.response}
                  </div>

                  {queryResponse.source_documents && queryResponse.source_documents.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Source Documents:</h4>
                      <div className="space-y-2">
                        {queryResponse.source_documents.map((doc, index) => (
                          <div key={index} className="text-sm text-gray-600 bg-white p-2 rounded border">
                            {doc}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 