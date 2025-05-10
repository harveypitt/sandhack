/**
 * LLM Analysis page component for location estimation
 */
import { Box, Heading, Text } from '@chakra-ui/react';
import ImageUploader from '../components/ImageUploader';

const LLMAnalysisPage = () => {
  return (
    <Box display="flex" flexDirection="column" alignItems="center" w="100%">
      <Heading size="lg" mb={4}>LLM Analysis</Heading>
      <Text fontSize="md" mb={6} textAlign="center" maxW="800px">
        This tool uses a Large Language Model to analyze your images and identify the likely location
        based on visual features like architecture, landscape, road markings, and other geographical indicators.
      </Text>
      
      <Box display="flex" justifyContent="center" alignItems="center" w="100%">
        <ImageUploader />
      </Box>
    </Box>
  );
};

export default LLMAnalysisPage; 