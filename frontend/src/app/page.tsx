"use client";

import ChunkViewer from '@/components/ChunkViewer';
import Header from '@/components/Header';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <ChunkViewer />
      </main>
    </div>
  );
}