/**
 * Drone Image Matcher Page
 * 
 * This page allows users to upload a drone image and a JSON file with coordinates,
 * then matches the drone image to find its location among the provided coordinates.
 */
import React, { useState } from 'react';
import {
  Box,
  Button,
  Heading,
  Text,
  VStack,
  Image,
  HStack,
  Progress,
  Badge,
  useToast,
  Switch,
  FormControl,
  FormLabel,
  Container,
  Grid,
  GridItem,
  Card,
  CardHeader,
  CardBody,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Link,
  Code,
} from '@chakra-ui/react';
import { matchDroneLocation, MatchResult } from '../api/droneMatcherApi';
import { ExternalLinkIcon } from '@chakra-ui/icons';

const DroneMatcherPage: React.FC = () => {
  const [droneImage, setDroneImage] = useState<File | null>(null);
  const [coordinatesFile, setCoordinatesFile] = useState<File | null>(null);
  const [dronePreview, setDronePreview] = useState<string | null>(null);
  const [useSimplified, setUseSimplified] = useState<boolean>(true);
  const [useContour, setUseContour] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [matchResults, setMatchResults] = useState<MatchResult | null>(null);
  
  const toast = useToast();
  
  // Handle drone image upload
  const handleDroneImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setDroneImage(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target && typeof e.target.result === 'string') {
          setDronePreview(e.target.result);
        }
      };
      reader.readAsDataURL(file);
    }
  };
  
  // Handle coordinates file upload
  const handleCoordinatesUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Validate the JSON file content
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          if (event.target && typeof event.target.result === 'string') {
            const jsonContent = JSON.parse(event.target.result);
            
            // Check if it's an array
            if (!Array.isArray(jsonContent)) {
              toast({
                title: 'Invalid JSON format',
                description: 'The coordinates file must contain a JSON array',
                status: 'error',
                duration: 5000,
              });
              return;
            }
            
            // Check if each item has lat and lon
            for (const coord of jsonContent) {
              if (!coord.lat || !coord.lon) {
                toast({
                  title: 'Invalid coordinates',
                  description: 'Each coordinate must have lat and lon properties',
                  status: 'error',
                  duration: 5000,
                });
                return;
              }
            }
            
            // JSON is valid, set the file
            setCoordinatesFile(file);
            
            toast({
              title: 'Coordinates file valid',
              description: `Found ${jsonContent.length} location(s) to check`,
              status: 'success',
              duration: 3000,
            });
          }
        } catch (error) {
          toast({
            title: 'Invalid JSON',
            description: 'The file does not contain valid JSON',
            status: 'error',
            duration: 5000,
          });
        }
      };
      reader.readAsText(file);
    }
  };
  
  // Start the matching process
  const handleStartMatching = async () => {
    if (!droneImage || !coordinatesFile) {
      toast({
        title: 'Missing files',
        description: 'Please upload both a drone image and a coordinates file',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    setIsLoading(true);
    setProgress(10);
    
    try {
      const formData = new FormData();
      formData.append('drone_image', droneImage);
      formData.append('coordinates_file', coordinatesFile);
      formData.append('simplify', useSimplified.toString());
      formData.append('use_contour', useContour.toString());
      
      // Update progress to indicate the request is sent
      setProgress(30);
      
      // Start the matching
      const result = await matchDroneLocation(formData);
      
      // Update progress
      setProgress(100);
      
      // Store and display the results
      setMatchResults(result);
      
      toast({
        title: 'Matching complete',
        description: `Found the best match with a score of ${result.best_match.score.toFixed(2)}%`,
        status: 'success',
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: 'Matching failed',
        description: 'An error occurred while matching the drone image',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  // Generate a link to view the location on Google Maps
  const getGoogleMapsLink = (coordinates: {lat: number, lon: number}) => {
    return `https://www.google.com/maps?q=${coordinates.lat},${coordinates.lon}`;
  };
  
  return (
    <Container maxW="container.xl" p={4}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading as="h1" size="xl" mb={2}>
            Drone Image Location Matcher
          </Heading>
          <Text fontSize="lg" color="gray.600">
            Match a drone image with satellite imagery to find its location
          </Text>
        </Box>
        
        {/* File Upload Section */}
        <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={6}>
          <GridItem>
            <Card variant="outline" height="100%">
              <CardHeader>
                <Heading size="md">Drone Image</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <Text fontSize="sm">Upload a drone image to match its location</Text>
                  <Button
                    as="label"
                    htmlFor="drone-upload"
                    colorScheme="blue"
                    cursor="pointer"
                    isDisabled={isLoading}
                  >
                    Upload Drone Image
                  </Button>
                  <input
                    id="drone-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleDroneImageUpload}
                    style={{ display: 'none' }}
                    disabled={isLoading}
                  />
                  {dronePreview && (
                    <Box borderWidth={1} borderRadius="md" p={2}>
                      <Image 
                        src={dronePreview} 
                        alt="Drone Preview" 
                        maxH="250px" 
                        mx="auto"
                      />
                      <Text mt={2} fontSize="sm" textAlign="center">
                        {droneImage?.name}
                      </Text>
                    </Box>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </GridItem>
          
          <GridItem>
            <Card variant="outline" height="100%">
              <CardHeader>
                <Heading size="md">Coordinates</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <Text fontSize="sm">Upload a JSON file with coordinates to check</Text>
                  <Box fontSize="xs" bg="gray.50" p={2} borderRadius="md">
                    <Text fontWeight="bold" mb={1}>Expected format:</Text>
                    <Code p={2} display="block" whiteSpace="pre" overflowX="auto" maxH="150px">
{`[
  {
    "lat": 51.6527061,
    "lon": -0.5245044,
    "description": "Location 1"
  },
  {
    "lat": 51.65279619,
    "lon": -0.5245044,
    "description": "Location 2"
  }
]`}
                    </Code>
                  </Box>
                  <Button
                    as="label"
                    htmlFor="coordinates-upload"
                    colorScheme="green"
                    cursor="pointer"
                    isDisabled={isLoading}
                  >
                    Upload Coordinates File
                  </Button>
                  <input
                    id="coordinates-upload"
                    type="file"
                    accept=".json,application/json"
                    onChange={handleCoordinatesUpload}
                    style={{ display: 'none' }}
                    disabled={isLoading}
                  />
                  {coordinatesFile && (
                    <Text fontSize="sm" textAlign="center">
                      Selected file: {coordinatesFile.name}
                    </Text>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </GridItem>
        </Grid>
        
        {/* Options and Action */}
        <Card variant="outline">
          <CardHeader>
            <Heading size="md">Matching Options</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="simplified-match" mb="0">
                  Use simplified matching (faster)
                </FormLabel>
                <Switch 
                  id="simplified-match" 
                  isChecked={useSimplified} 
                  onChange={() => setUseSimplified(!useSimplified)}
                  isDisabled={useContour || isLoading}
                  colorScheme="blue"
                />
              </FormControl>
              
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="contour-match" mb="0">
                  Use contour-based matching (less accurate)
                </FormLabel>
                <Switch 
                  id="contour-match" 
                  isChecked={useContour} 
                  onChange={() => setUseContour(!useContour)}
                  isDisabled={isLoading}
                  colorScheme="orange"
                />
              </FormControl>
              
              <Text fontSize="sm" color="gray.600">
                {useContour ? 
                  "Contour-based matching is faster but less accurate for rotated images." :
                  useSimplified ? 
                    "Simplified holistic matching provides a good balance of speed and accuracy." :
                    "Full holistic matching is the most accurate but slowest option."
                }
              </Text>
              
              <Button
                colorScheme="teal"
                size="lg"
                onClick={handleStartMatching}
                isLoading={isLoading}
                loadingText="Matching..."
                isDisabled={!droneImage || !coordinatesFile}
                mt={4}
              >
                Start Matching
              </Button>
              
              {isLoading && (
                <Box>
                  <Progress value={progress} size="sm" colorScheme="teal" borderRadius="md" />
                  <Text fontSize="sm" textAlign="center" mt={1}>
                    {progress < 30 ? "Preparing files..." : 
                     progress < 100 ? "Processing and matching..." : 
                     "Finalizing results..."}
                  </Text>
                </Box>
              )}
            </VStack>
          </CardBody>
        </Card>
        
        {/* Results Section */}
        {matchResults && (
          <Card variant="outline">
            <CardHeader>
              <Heading size="md">Matching Results</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={6} align="stretch">
                {/* Best Match */}
                <Box bg="green.50" p={4} borderRadius="md" borderWidth={1} borderColor="green.200">
                  <Heading size="sm" mb={3}>Best Match</Heading>
                  
                  {/* Coordinates and Score */}
                  <VStack align="start" spacing={2} mb={4}>
                    <HStack>
                      <Badge colorScheme="green" fontSize="md" px={2} py={1} borderRadius="md">
                        SCORE: {matchResults.best_match.score.toFixed(2)}%
                      </Badge>
                    </HStack>
                    <Text fontWeight="bold">Coordinates:</Text>
                    <Text>Latitude: {matchResults.best_match.coordinates.lat}</Text>
                    <Text>Longitude: {matchResults.best_match.coordinates.lon}</Text>
                    {matchResults.best_match.coordinates.description && (
                      <Text>Description: {matchResults.best_match.coordinates.description}</Text>
                    )}
                    <Link href={getGoogleMapsLink(matchResults.best_match.coordinates)} isExternal color="blue.500">
                      View on Google Maps <ExternalLinkIcon mx="2px" />
                    </Link>
                  </VStack>
                  
                  {/* Images Comparison */}
                  <Grid templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap={4}>
                    {/* Drone Image */}
                    <Box borderWidth={1} borderRadius="md" p={2} bg="white">
                      <Text fontSize="sm" fontWeight="bold" mb={2} textAlign="center">Drone Image</Text>
                      {dronePreview && (
                        <Image 
                          src={dronePreview} 
                          alt="Drone Image" 
                          maxH="250px" 
                          mx="auto"
                          display="block"
                        />
                      )}
                    </Box>
                    
                    {/* Satellite Image */}
                    <Box borderWidth={1} borderRadius="md" p={2} bg="white">
                      <Text fontSize="sm" fontWeight="bold" mb={2} textAlign="center">Satellite Match</Text>
                      {matchResults.best_match.satellite_image ? (
                        <Image 
                          src={`data:image/png;base64,${matchResults.best_match.satellite_image}`} 
                          alt="Satellite Match" 
                          maxH="250px"
                          mx="auto"
                          display="block"
                        />
                      ) : (
                        <Box 
                          height="200px" 
                          width="100%" 
                          display="flex"
                          alignItems="center"
                          justifyContent="center"
                          bg="gray.50"
                        >
                          <Text fontSize="sm" color="gray.500">Satellite image not available</Text>
                        </Box>
                      )}
                    </Box>
                  </Grid>
                </Box>
                
                {/* All Matches Table */}
                <Box>
                  <Heading size="sm" mb={3}>All Matches</Heading>
                  <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Rank</Th>
                          <Th>Score</Th>
                          <Th>Latitude</Th>
                          <Th>Longitude</Th>
                          <Th>Description</Th>
                          <Th>View</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {matchResults.all_matches.map((match, index) => (
                          <Tr key={index} bg={index === 0 ? "green.50" : undefined}>
                            <Td>{index + 1}</Td>
                            <Td>{match.score.toFixed(2)}%</Td>
                            <Td>{match.coordinates.lat}</Td>
                            <Td>{match.coordinates.lon}</Td>
                            <Td>{match.coordinates.description || "-"}</Td>
                            <Td>
                              <Link href={getGoogleMapsLink(match.coordinates)} isExternal color="blue.500">
                                <ExternalLinkIcon />
                              </Link>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                </Box>
                
                {/* Instructions for Interpretation */}
                <Box mt={6} p={4} borderRadius="md" bg="blue.50" borderWidth={1} borderColor="blue.200">
                  <Heading size="sm" mb={2}>Interpreting Results</Heading>
                  <Text fontSize="sm">
                    • The algorithm finds the best match between the drone image and satellite images from the provided coordinates.
                  </Text>
                  <Text fontSize="sm">
                    • A score of 100% indicates a perfect match, typically when using the exact same image.
                  </Text>
                  <Text fontSize="sm">
                    • For real drone images, scores around 10-20% might indicate a good match if there's a clear separation from other scores.
                  </Text>
                  <Text fontSize="sm">
                    • The simplified holistic matching is optimized for speed while maintaining good accuracy for non-rotated images.
                  </Text>
                </Box>
              </VStack>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Container>
  );
};

export default DroneMatcherPage; 