import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import styled from 'styled-components';
import axios from 'axios';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 2rem;
`;

const Title = styled.h1`
  color: #1c1917;
  text-align: center;
  margin-bottom: 3rem;
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
`;

const Card = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
  border: 1px solid #e7e5e4;
`;

const DropzoneContainer = styled.div`
  border: 3px dashed ${props => props.isDragActive ? '#047857' : '#d6d3d1'};
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: ${props => props.isDragActive ? 'rgba(4, 120, 87, 0.1)' : 'transparent'};

  &:hover {
    border-color: #047857;
    background: rgba(4, 120, 87, 0.05);
  }
`;

const DropzoneText = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #44403c;
  font-size: 1.1rem;
`;

const FileList = styled.div`
  margin-top: 2rem;
`;

const FileItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  margin: 0.5rem 0;
  background: rgba(4, 120, 87, 0.1);
  border-radius: 8px;
  border-left: 4px solid #047857;
`;

const FileInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: ${props => {
    switch (props.status) {
      case 'success': return '#22c55e';
      case 'error': return '#ef4444';
      case 'uploading': return '#f59e0b';
      default: return '#6b7280';
    }
  }};
`;

const Button = styled.button`
  background: #047857;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-family: inherit;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 1rem;

  &:hover {
    background: #065f46;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(4, 120, 87, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
`;

const StatCard = styled.div`
  background: rgba(4, 120, 87, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
  border: 1px solid rgba(4, 120, 87, 0.2);
`;

const StatNumber = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: #047857;
`;

const StatLabel = styled.div`
  color: #44403c;
  margin-top: 0.5rem;
  font-weight: 500;
`;

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

  return (
    <PageContainer>
      <Title>Import Industrial Data</Title>
      
      <Card>
        <DropzoneContainer {...getRootProps()} isDragActive={isDragActive}>
          <input {...getInputProps()} />
          <DropzoneText>
            <Upload size={48} color="#667eea" />
            {isDragActive ? (
              <p>Drop the CSV files here...</p>
            ) : (
              <>
                <p>Drag & drop CSV files here, or click to select files</p>
                <p style={{fontSize: '0.9rem', opacity: 0.7}}>
                  Supported formats: HMI sensor data, Tag configurations, Itera measurements
                </p>
              </>
            )}
          </DropzoneText>
        </DropzoneContainer>

        {files.length > 0 && (
          <FileList>
            <h3>Selected Files</h3>
            {files.map((fileItem) => (
              <FileItem key={fileItem.id}>
                <FileInfo>
                  <FileText size={20} color="#667eea" />
                  <div>
                    <div style={{fontWeight: '600'}}>{fileItem.name}</div>
                    <div style={{fontSize: '0.9rem', color: '#666'}}>
                      {(fileItem.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                </FileInfo>
                <StatusIndicator status={uploadStatus[fileItem.id]}>
                  {getStatusIcon(uploadStatus[fileItem.id])}
                  {getStatusText(uploadStatus[fileItem.id])}
                </StatusIndicator>
              </FileItem>
            ))}
            
            <Button 
              onClick={uploadAllFiles}
              disabled={files.every(f => uploadStatus[f.id] === 'success')}
            >
              Upload All Files
            </Button>
          </FileList>
        )}

        {importStats && (
          <StatsContainer>
            <StatCard>
              <StatNumber>{importStats.imports?.length || 0}</StatNumber>
              <StatLabel>Total Imports</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>
                {importStats.imports?.reduce((sum, imp) => sum + (imp.rows_imported || 0), 0) || 0}
              </StatNumber>
              <StatLabel>Total Rows</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>
                {importStats.imports?.filter(imp => imp.import_status === 'success').length || 0}
              </StatNumber>
              <StatLabel>Successful Imports</StatLabel>
            </StatCard>
          </StatsContainer>
        )}
      </Card>
    </PageContainer>
  );
};

export default ImportPage;