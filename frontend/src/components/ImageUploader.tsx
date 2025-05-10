/**
 * Component for uploading and analyzing images
 */
import { useState, useRef } from 'react';
import { 
  Box, 
  Button, 
  FormControl,
  FormLabel,
  Switch,
  VStack,
  HStack,
  Image,
  Text,
  useToast,
  Spinner,
  Heading,
} from '@chakra-ui/react';
import { analyzeImage } from '../api/api';

interface AnalysisResult {
  'estimated-location'?: string;
  'confidence'?: number;
  'visual-features'?: string[];
  'matching-regions'?: string[];
  'contours'?: any; // We would need to define a proper type for this
}

const ImageUploader = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isGlobalMode, setIsGlobalMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files ? event.target.files[0] : null;
    if (file) {
      if (!file.type.match('image.*')) {
        toast({
          title: 'Invalid file type',
          description: 'Please select an image file',
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
        return;
      }
      setSelectedFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      
      // Reset result
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      toast({
        title: 'No file selected',
        description: 'Please select an image to analyze',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsLoading(true);
    
    try {
      const data = await analyzeImage(selectedFile, isGlobalMode);
      setResult(data);
      toast({
        title: 'Analysis complete',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error analyzing image:', error);
      toast({
        title: 'Analysis failed',
        description: 'There was an error analyzing the image',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <VStack spacing={6} align="center" w="100%" maxW="800px" p={4}>
      <Heading size="lg">Image Location Analyzer</Heading>
      
      <FormControl display="flex" alignItems="center">
        <FormLabel htmlFor="global-mode" mb="0">
          Global Mode
        </FormLabel>
        <Switch 
          id="global-mode" 
          isChecked={isGlobalMode} 
          onChange={() => setIsGlobalMode(!isGlobalMode)}
        />
      </FormControl>
      
      <Box 
        w="100%" 
        h="300px" 
        border="2px dashed" 
        borderColor="gray.300"
        borderRadius="md"
        display="flex"
        alignItems="center"
        justifyContent="center"
        position="relative"
        overflow="hidden"
      >
        {preview ? (
          <Image 
            src={preview} 
            alt="Preview" 
            maxH="100%" 
            maxW="100%" 
            objectFit="contain"
          />
        ) : (
          <Text color="gray.500">No image selected</Text>
        )}
      </Box>
      
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        ref={fileInputRef}
        style={{ display: 'none' }}
      />
      
      <HStack spacing={4}>
        <Button 
          colorScheme="blue" 
          onClick={() => fileInputRef.current?.click()}
        >
          Select Image
        </Button>
        <Button 
          colorScheme="green" 
          onClick={handleAnalyze}
          isLoading={isLoading}
          loadingText="Analyzing"
          isDisabled={!selectedFile}
        >
          Analyze
        </Button>
        <Button onClick={handleReset}>Reset</Button>
      </HStack>
      
      {isLoading && (
        <Box textAlign="center">
          <Spinner size="xl" />
          <Text mt={2}>Analyzing image, this may take a moment...</Text>
        </Box>
      )}
      
      {result && (
        <Box 
          w="100%" 
          p={4} 
          bg="gray.50" 
          borderRadius="md"
          boxShadow="sm"
        >
          <Heading size="md" mb={2}>Analysis Results</Heading>
          
          <VStack align="start" spacing={2}>
            <Text><strong>Estimated Location:</strong> {result['estimated-location'] || 'Unknown'}</Text>
            <Text><strong>Confidence:</strong> {result['confidence'] ? `${result['confidence'] * 100}%` : 'Unknown'}</Text>
            
            {result['visual-features'] && (
              <Box>
                <Text><strong>Visual Features:</strong></Text>
                <Box pl={4}>
                  {result['visual-features'].map((feature, index) => (
                    <Text key={index}>• {feature}</Text>
                  ))}
                </Box>
              </Box>
            )}
            
            {result['matching-regions'] && (
              <Box>
                <Text><strong>Matching Regions:</strong></Text>
                <Box pl={4}>
                  {result['matching-regions'].map((region, index) => (
                    <Text key={index}>• {region}</Text>
                  ))}
                </Box>
              </Box>
            )}
          </VStack>
        </Box>
      )}
    </VStack>
  );
};

export default ImageUploader; 