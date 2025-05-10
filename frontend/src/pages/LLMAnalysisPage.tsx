/**
 * LLM Analysis page component for location estimation
 */
import { Box, Heading, Text, Container } from '@chakra-ui/react';
import ImageUploader from '../components/ImageUploader';

const LLMAnalysisPage = () => {
  return (
    <Container>
      <Box w="100%" textAlign="center">
        <Heading size="lg" mb={4}>LLM Analysis</Heading>
        <Text fontSize="md" mb={6} maxW="800px">
          This tool uses a Large Language Model to analyze your images and identify the likely location
          based on visual features like architecture, landscape, road markings, and other geographical indicators.
        </Text>
      </Box>
      
      <Box display="flex" justifyContent="center" alignItems="center" w="100%">
        <ImageUploader />
      </Box>
    </Container>
  );
};

export default LLMAnalysisPage; 