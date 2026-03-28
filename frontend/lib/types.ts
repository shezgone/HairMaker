export interface FacialFeatures {
  forehead_width: "narrow" | "medium" | "wide";
  jaw_width: "narrow" | "medium" | "wide";
  cheekbone_prominence: "low" | "medium" | "high";
  face_length: "short" | "medium" | "long";
}

export interface FaceAnalysis {
  face_shape: string;
  face_shape_confidence: number;
  facial_features: FacialFeatures;
  current_hair_estimate: string;
  recommended_style_tags: string[];
  avoid_style_tags: string[];
  consultation_summary: string;
}

export interface HairStyle {
  id: string;
  name: string;
  description: string;
  style_tags: string[];
  face_shapes: string[];
  face_shape_scores: Record<string, number>;
  hair_length: string;
  maintenance_level: number;
  reference_image_url: string;
  reference_images?: string[];
  simulation_prompt: string;
  is_active: boolean;
  gender: "male" | "female" | "unisex";
}

export interface Session {
  id: string;
  salon_id: string;
  designer_id: string;
  gender: "male" | "female";
  photo_url?: string;
  processed_photo_url?: string;
  face_analysis?: FaceAnalysis;
  selected_style_id?: string;
  consultation_notes?: string;
  status: "active" | "completed" | "archived";
  created_at: string;
}

export interface HairColor {
  name: string;
  description?: string;
  hex: string;
}

export interface PersonalColor {
  season: "spring" | "summer" | "autumn" | "winter";
  tone: "warm" | "cool";
  skin_tone: string;
  undertone_description: string;
  recommended_hair_colors: HairColor[];
  avoid_hair_colors: HairColor[];
  color_summary: string;
}

export interface SimulationJob {
  job_id: string;
  status: "pending" | "processing" | "done" | "error";
  result_url?: string;
  error?: string;
}
