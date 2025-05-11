/**
 * Main App component for the Location Estimation Frontend
 */
import { ChakraProvider, Box, Heading, Text, Flex, Button } from '@chakra-ui/react';
import { BrowserRouter as Router, Route, Routes, Link as RouterLink } from 'react-router-dom';
import LLMAnalysisPage from './pages/LLMAnalysisPage';
import HomePage from './pages/HomePage';
import ContourAnalysisPage from './pages/ContourAnalysisPage';
import DroneMatcherPage from './pages/DroneMatcherPage';
import { extendTheme } from '@chakra-ui/react';

// Create a custom theme to ensure no unexpected dark backgrounds
const theme = extendTheme({
  styles: {
    global: {
      'html, body, #root': {
        height: '100%',
        margin: 0,
        padding: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start', // Align content to the top
        backgroundColor: 'white',
        color: 'gray.800',
      },
    },
  },
  components: {
    Container: {
      baseStyle: {
        maxW: "container.lg", // Use a common container size
        width: "100%",
        px: 4, // Add some padding
        display: "flex",
        flexDirection: "column",
        alignItems: "center", // Center content within containers
      }
    }
  }
});

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        {/* The global styles should handle overall centering */}
        {/* The Box below is for main content structure */}
        <Box w="100%" maxW="1200px" px={{ base: 4, md: 8 }} py={8}>
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
              <Button as={RouterLink} to="/drone-matcher" colorScheme="green" variant="outline">
                Drone Matcher
              </Button>
            </Flex>
          </Box>
          
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/llm-analysis" element={<LLMAnalysisPage />} />
            <Route path="/contour-analysis" element={<ContourAnalysisPage />} />
            <Route path="/drone-matcher" element={<DroneMatcherPage />} />
          </Routes>
        </Box>
      </Router>
    </ChakraProvider>
  );
}

export default App; 