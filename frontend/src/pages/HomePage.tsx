/**
 * Home page component for the Location Estimation App
 */
import { Box, Heading, Text } from '@chakra-ui/react';

const HomePage = () => {
  return (
    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" w="100%">
      <Heading size="lg" mb={4}>Welcome to the Location Estimation App</Heading>
      <Text fontSize="lg" mb={6} textAlign="center">
        This application uses computer vision and LLM analysis to estimate the location of uploaded images.
      </Text>
      <Text fontSize="md" mb={2}>
        Available Tools:
      </Text>
      <Box border="1px" borderColor="gray.200" borderRadius="md" p={4} w="100%" maxW="600px">
        <Heading size="md" mb={2}>LLM Analysis</Heading>
        <Text>
          The LLM Analysis tool uses a Large Language Model to analyze visual features in your 
          images and estimate a likely geographic location based on those features.
        </Text>
        <Text mt={2} fontWeight="bold">
          Navigate to the LLM Analysis page to try this tool.
        </Text>
      </Box>
    </Box>
  );
};

export default HomePage; 