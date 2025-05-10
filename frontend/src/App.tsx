/**
 * Main App component for the Location Estimation Frontend
 */
import { ChakraProvider, Container, Box, Heading, Text } from '@chakra-ui/react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import LLMAnalysisPage from './pages/LLMAnalysisPage';
import HomePage from './pages/HomePage';

function App() {
  return (
    <ChakraProvider>
      <Router>
        <Container maxW="container.xl" py={8}>
          <Box textAlign="center" mb={8}>
            <Heading as="h1" size="xl" mb={2}>
              Location Estimation App
            </Heading>
            <Text fontSize="lg" color="gray.600">
              Upload an image to estimate its location using computer vision and LLM analysis
            </Text>
            <Box mt={4} display="flex" justifyContent="center" gap={4}>
              <Link to="/">Home</Link>
              <Link to="/llm-analysis">LLM Analysis</Link>
            </Box>
          </Box>
          
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/llm-analysis" element={<LLMAnalysisPage />} />
          </Routes>
        </Container>
      </Router>
    </ChakraProvider>
  );
}

export default App; 