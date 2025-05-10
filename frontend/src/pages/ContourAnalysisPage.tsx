/**
 * Contour Analysis Page
 * 
 * This page allows users to upload one drone image and up to four satellite images,
 * then performs contour extraction and matching to find the best match.
 */
import React, { useState } from 'react';
import {
  Box,
  Button,
  Heading,
  Text,
  VStack,
  Image,
  Grid,
  GridItem,
  Progress,
  Flex,
  Badge,
  useToast,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
  Tooltip,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import { extractContours, matchContours } from '../api/contourApi';

interface MatchResult {
  image_index: number;
  match_score: number;
  satellite_image: string;
  visualization: string;
  holistic_visualization: string;
  contour_visualization: string;
  contour_count: number;
  filename: string;
}

interface ContourMatchResult {
  drone_image: string;
  drone_contour_count: number;
  drone_contour_visualization: string;
  satellite_results: MatchResult[];
  best_match_index: number | null;
  best_match_score: number;
}

const ContourAnalysisPage: React.FC = () => {
  const [droneImage, setDroneImage] = useState<File | null>(null);
  const [satelliteImages, setSatelliteImages] = useState<File[]>([]);
  const [dronePreview, setDronePreview] = useState<string | null>(null);
  const [satellitePreviews, setSatellitePreviews] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeStep, setActiveStep] = useState<number>(0);
  const [droneContours, setDroneContours] = useState<any | null>(null);
  const [matchResults, setMatchResults] = useState<ContourMatchResult | null>(null);
  const [contourThreshold, setContourThreshold] = useState<number>(50);
  const [showThresholdTooltip, setShowThresholdTooltip] = useState<boolean>(false);
  
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
  
  // Handle satellite images upload
  const handleSatelliteImagesUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files).slice(0, 4); // Max 4 images
      setSatelliteImages(files);
      
      // Create previews
      const previews: string[] = [];
      files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target && typeof e.target.result === 'string') {
            previews.push(e.target.result);
            if (previews.length === files.length) {
              setSatellitePreviews(previews);
            }
          }
        };
        reader.readAsDataURL(file);
      });
    }
  };
  
  // Start contour extraction
  const handleExtractContours = async () => {
    if (!droneImage) {
      toast({
        title: 'No drone image selected',
        description: 'Please upload a drone image first',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    setIsLoading(true);
    setActiveStep(1);
    
    try {
      const formData = new FormData();
      formData.append('file', droneImage);
      formData.append('threshold', contourThreshold.toString());
      
      const result = await extractContours(formData);
      if (result) {
        setDroneContours(result);
        setActiveStep(2);
      }
    } catch (error) {
      toast({
        title: 'Extraction failed',
        description: 'Failed to extract contours from the drone image',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  // Start contour matching
  const handleMatchContours = async () => {
    if (!droneImage || satelliteImages.length === 0) {
      toast({
        title: 'Missing images',
        description: 'Please upload both drone and satellite images',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    setIsLoading(true);
    setActiveStep(3);
    
    try {
      const formData = new FormData();
      formData.append('drone_image', droneImage);
      
      satelliteImages.forEach((image) => {
        formData.append('satellite_images', image);
      });
      
      // Add the same threshold used in extraction for consistency
      formData.append('threshold', contourThreshold.toString());
      
      const result = await matchContours(formData);
      if (result) {
        setMatchResults(result);
        setActiveStep(4);
      }
    } catch (error) {
      toast({
        title: 'Matching failed',
        description: 'Failed to match contours between images',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Box width="100%" display="flex" flexDirection="column" alignItems="center">
      <VStack spacing={6} width="100%" maxW="800px" align="center">
        <Heading size="md" mb={2} mt={6}>Contour Analysis</Heading>
        <Text mb={4} textAlign="center">
          Upload a drone/UAV image and up to 4 satellite images to extract and match contours for location estimation
        </Text>
        
        {/* Progress steps */}
        <Box mb={6} width="100%" maxW="800px">
          <Progress 
            value={(activeStep / 4) * 100} 
            size="sm" 
            colorScheme="teal" 
            borderRadius="md"
            mb={2}
          />
          <Flex justify="space-between">
            <Text fontSize="sm" fontWeight={activeStep >= 0 ? "bold" : "normal"} color={activeStep >= 0 ? "teal.500" : "gray.500"}>
              Upload
            </Text>
            <Text fontSize="sm" fontWeight={activeStep >= 1 ? "bold" : "normal"} color={activeStep >= 1 ? "teal.500" : "gray.500"}>
              Extract
            </Text>
            <Text fontSize="sm" fontWeight={activeStep >= 2 ? "bold" : "normal"} color={activeStep >= 2 ? "teal.500" : "gray.500"}>
              Process
            </Text>
            <Text fontSize="sm" fontWeight={activeStep >= 3 ? "bold" : "normal"} color={activeStep >= 3 ? "teal.500" : "gray.500"}>
              Match
            </Text>
            <Text fontSize="sm" fontWeight={activeStep >= 4 ? "bold" : "normal"} color={activeStep >= 4 ? "teal.500" : "gray.500"}>
              Results
            </Text>
          </Flex>
        </Box>
        
        {/* Image upload section */}
        <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={6} mb={6} width="100%">
          <GridItem>
            <VStack spacing={4} align="start" borderWidth={1} borderRadius="md" p={4} height="100%">
              <Heading size="md">Drone Image</Heading>
              <Text fontSize="sm">Upload a single drone or UAV image</Text>
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
                <Box borderWidth={1} borderRadius="md" p={2} width="100%">
                  <Image 
                    src={dronePreview} 
                    alt="Drone Preview" 
                    maxH="200px" 
                    mx="auto"
                  />
                  <Text mt={2} fontSize="sm" textAlign="center">
                    {droneImage?.name}
                  </Text>
                </Box>
              )}
            </VStack>
          </GridItem>
          
          <GridItem>
            <VStack spacing={4} align="start" borderWidth={1} borderRadius="md" p={4} height="100%">
              <Heading size="md">Satellite Images</Heading>
              <Text fontSize="sm">Upload up to 4 satellite images</Text>
              <Button
                as="label"
                htmlFor="satellite-upload"
                colorScheme="purple"
                cursor="pointer"
                isDisabled={isLoading}
              >
                Upload Satellite Images
              </Button>
              <input
                id="satellite-upload"
                type="file"
                accept="image/*"
                multiple
                onChange={handleSatelliteImagesUpload}
                style={{ display: 'none' }}
                disabled={isLoading}
              />
              {satellitePreviews.length > 0 && (
                <Grid templateColumns="repeat(2, 1fr)" gap={2} width="100%">
                  {satellitePreviews.map((preview, index) => (
                    <GridItem key={index}>
                      <Box borderWidth={1} borderRadius="md" p={2}>
                        <Image 
                          src={preview} 
                          alt={`Satellite ${index + 1}`} 
                          maxH="100px" 
                          mx="auto"
                        />
                        <Text mt={1} fontSize="xs" textAlign="center" noOfLines={1}>
                          {satelliteImages[index]?.name}
                        </Text>
                      </Box>
                    </GridItem>
                  ))}
                </Grid>
              )}
            </VStack>
          </GridItem>
        </Grid>
        
        {/* Action buttons and Threshold slider */}
        <Box width="100%" maxW="800px" mb={6}>
          <VStack spacing={6} align="start">
            {/* Contour Threshold slider - before Extract button */}
            <Box width="100%">
              <Text mb={2}>Contour Detection Threshold: {contourThreshold}</Text>
              <Slider
                id="threshold-slider"
                min={0}
                max={100}
                step={5}
                value={contourThreshold}
                onChange={(val) => setContourThreshold(val)}
                onMouseEnter={() => setShowThresholdTooltip(true)}
                onMouseLeave={() => setShowThresholdTooltip(false)}
                mb={2}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <Tooltip
                  hasArrow
                  bg='teal.500'
                  color='white'
                  placement='top'
                  isOpen={showThresholdTooltip}
                  label={`${contourThreshold}`}
                >
                  <SliderThumb />
                </Tooltip>
                <SliderMark value={25} mt={2} fontSize="sm">25</SliderMark>
                <SliderMark value={50} mt={2} fontSize="sm">50</SliderMark>
                <SliderMark value={75} mt={2} fontSize="sm">75</SliderMark>
              </Slider>
              <Text fontSize="sm" color="gray.600">
                Adjust contour strength and detail. Lower values detect fewer but stronger contours.
              </Text>
            </Box>
            
            <Button
              width="100%"
              colorScheme="teal"
              onClick={handleExtractContours}
              isLoading={isLoading && activeStep === 1}
              loadingText="Extracting..."
              isDisabled={!droneImage || isLoading}
            >
              Extract Contours
            </Button>
            
            <Button
              width="100%"
              colorScheme="orange"
              onClick={handleMatchContours}
              isLoading={isLoading && activeStep === 3}
              loadingText="Matching..."
              isDisabled={!droneImage || satelliteImages.length === 0 || isLoading}
            >
              Match Contours
            </Button>
          </VStack>
        </Box>
      
        {/* Contour extraction results */}
        {droneContours && (
          <Box mb={8} width="100%">
            <Heading size="md" mb={4}>Contour Extraction Results</Heading>
            <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={6}>
              <GridItem>
                <Box borderWidth={1} borderRadius="md" p={4}>
                  <Heading size="sm" mb={2}>Original Image</Heading>
                  <Image 
                    src={`data:image/jpeg;base64,${droneContours.original_image}`} 
                    alt="Original Image" 
                    maxH="300px" 
                    mx="auto"
                  />
                </Box>
              </GridItem>
              
              <GridItem>
                <Box borderWidth={1} borderRadius="md" p={4}>
                  <Heading size="sm" mb={2}>Contour Visualization</Heading>
                  <Image 
                    src={`data:image/jpeg;base64,${droneContours.contour_visualization}`} 
                    alt="Contour Visualization" 
                    maxH="300px" 
                    mx="auto"
                  />
                </Box>
              </GridItem>
            </Grid>
            
            <Box mt={4}>
              <Heading size="sm" mb={2}>Detected Features</Heading>
              {droneContours.major_features.map((feature: string, index: number) => (
                <Badge key={index} m={1} colorScheme="teal">{feature}</Badge>
              ))}
            </Box>
          </Box>
        )}
        
        {/* Satellite Images Preview with Tabs - shown after extraction but before matching */}
        {droneContours && satelliteImages.length > 0 && !matchResults && (
          <Box mb={8} width="100%">
            <Heading size="md" mb={4}>Satellite Images</Heading>
            <Text mb={4}>Click "Match Contours" to compare the drone image with these satellite images.</Text>
            
            <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={6}>
              {satelliteImages.map((image, index) => (
                <GridItem key={index}>
                  <Box borderWidth={1} borderRadius="md" p={4}>
                    <Heading size="sm" mb={2}>{image.name}</Heading>
                    <Tabs variant="soft-rounded" colorScheme="teal" size="sm">
                      <TabList>
                        <Tab>Image</Tab>
                      </TabList>
                      <TabPanels>
                        <TabPanel p={2}>
                          <Image 
                            src={satellitePreviews[index]} 
                            alt={`Satellite ${index + 1}`} 
                            maxH="200px" 
                            mx="auto"
                          />
                        </TabPanel>
                      </TabPanels>
                    </Tabs>
                  </Box>
                </GridItem>
              ))}
            </Grid>
          </Box>
        )}
        
        {/* Contour matching results */}
        {matchResults && (
          <Box mb={8} width="100%">
            <Heading size="md" mb={4}>Contour Matching Results</Heading>
            
            {/* Best match */}
            {matchResults.best_match_index !== null && (
              <Box mb={6}>
                <Heading size="sm" mb={2}>
                  Best Match
                  <Badge ml={2} colorScheme="green">
                    {matchResults.best_match_score.toFixed(2)}% Match
                  </Badge>
                </Heading>
                
                <Tabs variant="enclosed" colorScheme="teal">
                  <TabList>
                    <Tab>Comparison</Tab>
                    <Tab>Holistic</Tab>
                    <Tab>Contours</Tab>
                  </TabList>
                  <TabPanels>
                    <TabPanel p={0} pt={4}>
                      <Box borderWidth={2} borderColor="green.500" borderRadius="md" p={4}>
                        <Image 
                          src={`data:image/jpeg;base64,${matchResults.satellite_results[matchResults.best_match_index].visualization}`} 
                          alt="Best Match Visualization" 
                          maxH="400px" 
                          mx="auto"
                        />
                        <Text mt={2} fontWeight="bold" textAlign="center">
                          {matchResults.satellite_results[matchResults.best_match_index].filename}
                        </Text>
                      </Box>
                    </TabPanel>
                    <TabPanel p={0} pt={4}>
                      <Box borderWidth={2} borderColor="green.500" borderRadius="md" p={4}>
                        <Image 
                          src={`data:image/jpeg;base64,${matchResults.satellite_results[matchResults.best_match_index].holistic_visualization}`} 
                          alt="Holistic Visualization" 
                          maxH="400px" 
                          mx="auto"
                          bgColor="black"
                        />
                        <Text mt={2} fontWeight="bold" textAlign="center">
                          Holistic Contour Match - {matchResults.satellite_results[matchResults.best_match_index].filename}
                        </Text>
                      </Box>
                    </TabPanel>
                    <TabPanel p={0} pt={4}>
                      <Box borderWidth={2} borderColor="green.500" borderRadius="md" p={4}>
                        <Image 
                          src={`data:image/jpeg;base64,${matchResults.satellite_results[matchResults.best_match_index].contour_visualization}`} 
                          alt="Contour Visualization" 
                          maxH="400px" 
                          mx="auto"
                        />
                        <Text mt={2} fontWeight="bold" textAlign="center">
                          Contour Visualization - {matchResults.satellite_results[matchResults.best_match_index].filename}
                        </Text>
                      </Box>
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </Box>
            )}
            
            {/* All matches */}
            <Heading size="sm" mb={4}>All Matches</Heading>
            <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={6}>
              {matchResults.satellite_results.map((result, index) => (
              <GridItem key={index}>
                <Box 
                  borderWidth={1} 
                  borderRadius="md" 
                  p={4}
                  borderColor={matchResults.best_match_index === result.image_index ? "green.500" : "gray.200"}
                  bg={matchResults.best_match_index === result.image_index ? "green.50" : "white"}
                >
                  <Flex justify="space-between" mb={2}>
                    <Heading size="xs">{result.filename}</Heading>
                    <Badge colorScheme={result.match_score > 70 ? "green" : result.match_score > 40 ? "yellow" : "red"}>
                      {result.match_score.toFixed(2)}% Match
                    </Badge>
                  </Flex>
                  
                  <Tabs variant="soft-rounded" colorScheme="teal" size="sm">
                    <TabList>
                      <Tab>Comparison</Tab>
                      <Tab>Holistic</Tab>
                      <Tab>Contours</Tab>
                    </TabList>
                    <TabPanels>
                      <TabPanel p={2}>
                        <Image 
                          src={`data:image/jpeg;base64,${result.visualization}`} 
                          alt={`Match ${index + 1}`} 
                          maxH="200px" 
                          mx="auto"
                        />
                      </TabPanel>
                      <TabPanel p={2}>
                        <Image 
                          src={`data:image/jpeg;base64,${result.holistic_visualization}`} 
                          alt={`Holistic ${index + 1}`} 
                          maxH="200px" 
                          mx="auto"
                          bgColor="black"
                        />
                      </TabPanel>
                      <TabPanel p={2}>
                        <Image 
                          src={`data:image/jpeg;base64,${result.contour_visualization}`} 
                          alt={`Contours ${index + 1}`} 
                          maxH="200px" 
                          mx="auto"
                        />
                      </TabPanel>
                    </TabPanels>
                  </Tabs>
                  
                  <Text mt={2} fontSize="sm">
                    Contours detected: {result.contour_count}
                  </Text>
                </Box>
              </GridItem>
              ))}
            </Grid>
          </Box>
        )}
        
        {/* Footer with information about the app */}
        <Box 
          as="footer" 
          mt={10} 
          py={6} 
          borderTopWidth={1} 
          borderTopColor="gray.200"
          width="100%"
          textAlign="center"
        >
          <Text fontSize="sm" color="gray.500">
            Location Estimation App &copy; {new Date().getFullYear()} - Contour Analysis Module
          </Text>
          <Text fontSize="xs" color="gray.400" mt={1}>
            Computer vision powered location estimation using contour matching technology
          </Text>
        </Box>
      </VStack>
    </Box>
  );
};

export default ContourAnalysisPage; 