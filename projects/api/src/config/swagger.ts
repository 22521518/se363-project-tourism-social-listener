import swaggerJsdoc from 'swagger-jsdoc';

const options: swaggerJsdoc.Options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Tourism Social Listener API',
      version: '1.0.0',
      description: 'API for accessing tourism social listening data including location extractions, intentions, and traveling types.',
      contact: {
        name: 'API Support',
      },
    },
    servers: [
      {
        url: 'http://localhost:3001',
        description: 'Development server',
      },
    ],
    components: {
      schemas: {
        GeographyStats: {
          type: 'object',
          description: 'Aggregated location statistics by geographic region (relative to Vietnam as origin)',
          properties: {
            name: {
              type: 'string',
              description: 'Geographic category: Domestic (Vietnam), Regional (South East Asia), or International',
              enum: ['Domestic', 'Regional', 'International'],
              example: 'Domestic',
            },
            value: {
              type: 'integer',
              description: 'Count of locations in this category',
              example: 5200,
            },
            color: {
              type: 'string',
              description: 'Hex color code for visualization',
              example: '#3b82f6',
            },
          },
          required: ['name', 'value', 'color'],
        },
        GeographyStatsResponse: {
          type: 'object',
          properties: {
            success: {
              type: 'boolean',
              description: 'Whether the request was successful',
              example: true,
            },
            data: {
              type: 'array',
              items: {
                $ref: '#/components/schemas/GeographyStats',
              },
            },
          },
        },
        ErrorResponse: {
          type: 'object',
          properties: {
            success: {
              type: 'boolean',
              example: false,
            },
            error: {
              type: 'string',
              description: 'Error message',
              example: 'Failed to fetch geography stats',
            },
          },
        },
        LocationType: {
          type: 'string',
          enum: ['country', 'city', 'state', 'province', 'landmark', 'unknown'],
          description: 'Type of extracted location',
        },
        Location: {
          type: 'object',
          description: 'A single extracted location',
          properties: {
            name: {
              type: 'string',
              description: 'Name of the location',
              example: 'Vietnam',
            },
            type: {
              $ref: '#/components/schemas/LocationType',
            },
            confidence: {
              type: 'number',
              format: 'float',
              minimum: 0,
              maximum: 1,
              description: 'Confidence score for the extraction',
              example: 0.95,
            },
          },
          required: ['name', 'type', 'confidence'],
        },
        LocationExtraction: {
          type: 'object',
          description: 'Complete location extraction record',
          properties: {
            id: {
              type: 'string',
              format: 'uuid',
              description: 'Unique identifier',
            },
            source_id: {
              type: 'string',
              description: 'ID of the source content (e.g., YouTube comment ID)',
            },
            source_type: {
              type: 'string',
              description: 'Type of source (e.g., youtube_comment)',
            },
            raw_text: {
              type: 'string',
              description: 'Original text that was analyzed',
            },
            locations: {
              type: 'array',
              items: {
                $ref: '#/components/schemas/Location',
              },
            },
            primary_location: {
              $ref: '#/components/schemas/Location',
              nullable: true,
            },
            overall_score: {
              type: 'number',
              format: 'float',
              description: 'Overall confidence score',
            },
            is_approved: {
              type: 'boolean',
              description: 'Whether a human has approved this extraction',
            },
            created_at: {
              type: 'string',
              format: 'date-time',
            },
          },
        },
      },
    },
  },
  apis: ['./src/controllers/*.ts'],
};

export const swaggerSpec = swaggerJsdoc(options);
