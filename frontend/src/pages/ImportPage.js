import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';

const ImportPage = () => {
  const [files, setFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState({});
  const [importStats, setImportStats] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    multiple: true
  });

  const uploadFile = async (fileItem) => {
    const { file, id } = fileItem;
    setUploadStatus(prev => ({ ...prev, [id]: 'uploading' }));

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/import-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadStatus(prev => ({ ...prev, [id]: 'success' }));
      
      // Update import stats
      fetchImportStats();
      
      return response.data;
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus(prev => ({ ...prev, [id]: 'error' }));
      throw error;
    }
  };

  const uploadAllFiles = async () => {
    const pendingFiles = files.filter(f => !uploadStatus[f.id]);
    
    for (const fileItem of pendingFiles) {
      try {
        await uploadFile(fileItem);
      } catch (error) {
        console.error(`Failed to upload ${fileItem.name}:`, error);
      }
    }
  };

  const fetchImportStats = async () => {
    try {
      const response = await axios.get('/import-status');
      setImportStats(response.data);
    } catch (error) {
      console.error('Failed to fetch import stats:', error);
    }
  };

  React.useEffect(() => {
    fetchImportStats();
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle size={20} />;
      case 'error':
        return <XCircle size={20} />;
      case 'uploading':
        return <AlertCircle size={20} />;
      default:
        return <FileText size={20} />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'success':
        return 'Uploaded Successfully';
      case 'error':
        return 'Upload Failed';
      case 'uploading':
        return 'Uploading...';
      default:
        return 'Ready to Upload';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'uploading':
        return 'text-amber-600';
      default:
        return 'text-stone-500';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-4xl font-bold text-stone-900 text-center mb-12 tracking-tight">
        Import Industrial Data
      </h1>
      
      <Card>
        <CardContent className="pt-6">
          <div 
            {...getRootProps()} 
            className={`border-3 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
              isDragActive 
                ? 'border-primary-700 bg-primary-50' 
                : 'border-stone-300 hover:border-primary-700 hover:bg-primary-50/50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4 text-stone-700 text-lg">
              <Upload size={48} className="text-primary-700" />
              {isDragActive ? (
                <p>Drop the CSV files here...</p>
              ) : (
                <>
                  <p>Drag & drop CSV files here, or click to select files</p>
                  <p className="text-sm opacity-70">
                    Supported formats: HMI sensor data, Tag configurations, Itera measurements
                  </p>
                </>
              )}
            </div>
          </div>

          {files.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-stone-800 mb-4">Selected Files</h3>
              {files.map((fileItem) => (
                <div 
                  key={fileItem.id} 
                  className="flex items-center justify-between p-4 my-2 bg-primary-50 rounded-lg border-l-4 border-primary-700"
                >
                  <div className="flex items-center gap-4">
                    <FileText size={20} className="text-primary-700" />
                    <div>
                      <div className="font-semibold text-stone-900">{fileItem.name}</div>
                      <div className="text-sm text-stone-600">
                        {(fileItem.size / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  </div>
                  <div className={`flex items-center gap-2 ${getStatusColor(uploadStatus[fileItem.id])}`}>
                    {getStatusIcon(uploadStatus[fileItem.id])}
                    <span className="font-medium">{getStatusText(uploadStatus[fileItem.id])}</span>
                  </div>
                </div>
              ))}
              
              <Button 
                onClick={uploadAllFiles}
                disabled={files.every(f => uploadStatus[f.id] === 'success')}
                className="mt-4 bg-primary-700 hover:bg-primary-800 text-white font-semibold"
              >
                Upload All Files
              </Button>
            </div>
          )}

          {importStats && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
              <div className="bg-primary-50 p-6 rounded-xl text-center border border-primary-200">
                <div className="text-3xl font-bold text-primary-700">
                  {importStats.imports?.length || 0}
                </div>
                <div className="text-stone-700 mt-2 font-medium">Total Imports</div>
              </div>
              <div className="bg-primary-50 p-6 rounded-xl text-center border border-primary-200">
                <div className="text-3xl font-bold text-primary-700">
                  {importStats.imports?.reduce((sum, imp) => sum + (imp.rows_imported || 0), 0) || 0}
                </div>
                <div className="text-stone-700 mt-2 font-medium">Total Rows</div>
              </div>
              <div className="bg-primary-50 p-6 rounded-xl text-center border border-primary-200">
                <div className="text-3xl font-bold text-primary-700">
                  {importStats.imports?.filter(imp => imp.import_status === 'success').length || 0}
                </div>
                <div className="text-stone-700 mt-2 font-medium">Successful Imports</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ImportPage;