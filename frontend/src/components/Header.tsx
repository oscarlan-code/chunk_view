"use client";

export default function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CV</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">PDF Highlight Viewer</h1>
          </div>
          <div className="text-sm text-gray-500">
            PDF Coordinate-Based Highlighting Tool
          </div>
        </div>
      </div>
    </header>
  );
}
