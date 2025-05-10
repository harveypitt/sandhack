/**
 * Main App component for the Location Estimation Frontend
 */
import { ChakraProvider, Box, Heading, Text, Flex, Button, Center } from '@chakra-ui/react';
import { BrowserRouter as Router, Route, Routes, Link as RouterLink } from 'react-router-dom';
import LLMAnalysisPage from './pages/LLMAnalysisPage';
import HomePage from './pages/HomePage';
import ContourAnalysisPage from './pages/ContourAnalysisPage';
import { extendTheme } from '@chakra-ui/react';

// Create a custom theme to ensure no unexpected dark backgrounds
const theme = extendTheme({
  styles: {
    global: {
      'html, body': {
        backgroundColor: 'white',
        color: 'gray.800',
        minHeight: '100vh',
      },
    },
  },
  components: {
    Container: {
      baseStyle: {
        maxW: "800px",
        mx: "auto",
        px: 4,
      }
    }
  }
});

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        <Center w="100%" minH="100vh" bg="white">
          <Box w="100%" maxW="800px" px={4}>
            <Box textAlign="center" mb={8}>
              <Heading as="h1" size="xl" mb={2}>
                Location Estimation App
              </Heading>
              <Text fontSize="lg" color="gray.600" mb={6}>
                Upload an image to estimate its location using computer vision and LLM analysis
              </Text>
              <Flex mt={4} justify="center" gap={2}>
                <Button as={RouterLink} to="/" colorScheme="teal" variant="outline">
                  Home
                </Button>
                <Button as={RouterLink} to="/llm-analysis" colorScheme="blue" variant="outline">
                  LLM Analysis
                </Button>
                <Button as={RouterLink} to="/contour-analysis" colorScheme="purple" variant="outline">
                  Contour Analysis
                </Button>
              </Flex>
            </Box>
            
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/llm-analysis" element={<LLMAnalysisPage />} />
              <Route path="/contour-analysis" element={<ContourAnalysisPage />} />
            </Routes>
          </Box>
        </Center>
      </Router>
    </ChakraProvider>
  );
}

export default App; 