import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

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
  simulate: boolean;
}

export interface GenerateResponse {
  cards: Flashcard[];
}

export const generateCards = async (req: GenerateRequest): Promise<Flashcard[]> => {
  try {
    const response = await axios.post<GenerateResponse>(`${API_BASE_URL}/generate`, req);
    return response.data.cards;
  } catch (error) {
    console.error('Error generating cards:', error);
    throw error;
  }
};
