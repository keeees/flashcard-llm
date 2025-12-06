import axios from 'axios';
import { logger } from '../utils/logger';

const API_BASE_URL = '/api';

export interface Flashcard {
  question: string;
  answer: string;
  tags: string[];
  type: string;
}

export interface GenerateRequest {
  text: string;
  difficulty: string;
  card_type: string;
  total_cards: number;
}

export interface GenerateResponse {
  cards: Flashcard[];
}

export const generateCards = async (req: GenerateRequest): Promise<Flashcard[]> => {
  logger.info('Calling generateCards API', req);
  try {
    const response = await axios.post<GenerateResponse>(`${API_BASE_URL}/generate`, req);
    logger.info('API response received', { status: response.status, cardsCount: response.data.cards.length });
    return response.data.cards;
  } catch (error) {
    logger.error('Error generating cards:', error);
    throw error;
  }
};
