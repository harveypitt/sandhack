/**
 * Main App component for the Location Estimation Frontend
 */
import { ChakraProvider, Container, Box, Heading, Text } from '@chakra-ui/react';
import ImageUploader from './components/ImageUploader';

function App() {
  return (
    <ChakraProvider>
      <Container maxW="container.xl" py={8}>
        <Box textAlign="center" mb={8}>
          <Heading as="h1" size="xl" mb={2}>
            Location Estimation App
          </Heading>
          <Text fontSize="lg" color="gray.600">
            Upload an image to estimate its location using computer vision and LLM analysis
          </Text>
        </Box>
        
        <Box display="flex" justifyContent="center" alignItems="center">
          <ImageUploader />
        </Box>
      </Container>
    </ChakraProvider>
  );
}

export default App; 