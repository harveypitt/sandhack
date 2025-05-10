/**
 * Home page component for the Location Estimation App
 */
import { Box, Heading, Text, VStack, Link, Center } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';

const HomePage = () => {
  return (
    <Center w="100%">
      <VStack w="100%" spacing={6} align="center">
        <Box textAlign="center">
          <Heading size="lg" mb={4}>Welcome to the Location Estimation App</Heading>
          <Text fontSize="lg" mb={6}>
            This application uses computer vision and LLM analysis to estimate the location of uploaded images.
          </Text>
        </Box>
        
        <Text fontSize="md" mb={2}>
          Available Tools:
        </Text>
        
        <VStack spacing={4} w="100%" maxW="600px">
          <Box border="1px" borderColor="gray.200" borderRadius="md" p={4} w="100%">
            <Heading size="md" mb={2}>LLM Analysis</Heading>
            <Text>
              The LLM Analysis tool uses a Large Language Model to analyze visual features in your 
              images and estimate a likely geographic location based on those features.
            </Text>
            <Link as={RouterLink} to="/llm-analysis" color="teal.500" fontWeight="bold" mt={2} display="block">
              Try LLM Analysis
            </Link>
          </Box>
          
          <Box border="1px" borderColor="gray.200" borderRadius="md" p={4} w="100%">
            <Heading size="md" mb={2}>Contour Analysis</Heading>
            <Text>
              The Contour Analysis tool extracts and matches contours between drone/UAV images and 
              satellite imagery to find the best match and estimate the location.
            </Text>
            <Text mt={2} fontSize="sm">
              Upload one drone image and up to four satellite images to compare and find the best match 
              based on geographical features.
            </Text>
            <Link as={RouterLink} to="/contour-analysis" color="teal.500" fontWeight="bold" mt={2} display="block">
              Try Contour Analysis
            </Link>
          </Box>
        </VStack>
      </VStack>
    </Center>
  );
};

export default HomePage; 