export type Assignment = {
  editable: boolean;
  pk: string;
  question_pks: number[]; // eslint-disable-line camelcase
  title: string;
};

export type AssignmentForm = {
  conclusion_page: string; // eslint-disable-line camelcase
  description: string;
  identifier: string;
  intro_page: string; // eslint-disable-line camelcase
  title: string;
};

export type AssignmentCreate = {
  conclusion_page: string; // eslint-disable-line camelcase
  description: string;
  pk: string;
  intro_page: string; // eslint-disable-line camelcase
  title: string;
};

export type Question = {
  answer_count: number; // eslint-disable-line camelcase
  answer_style: number; // eslint-disable-line camelcase
  answerchoice_set: { correct: boolean; text: string }[]; // eslint-disable-line camelcase
  assignment_count: number; // eslint-disable-line camelcase
  category: { title: string }[];
  collections?: { title: string; url: string }[];
  deleted: boolean;
  difficulty: { score?: number | null; label: string };
  discipline: { title: string };
  featured: boolean;
  flag_reasons?: { flag_reason__count: number; flag_reason__title: string }[]; // eslint-disable-line camelcase
  frequency: {
    first_choice: Record<string, number>; // eslint-disable-line camelcase
    second_choice: Record<string, number>; // eslint-disable-line camelcase
  };
  image: string;
  image_alt_text: string; // eslint-disable-line camelcase
  is_not_flagged?: boolean; // eslint-disable-line camelcase
  is_not_missing_answer_choices?: boolean; // eslint-disable-line camelcase
  is_not_missing_sample_answers?: boolean; // eslint-disable-line camelcase
  matrix: { easy: number; hard: number; tricky: number; peer: number };
  // eslint-disable-next-line camelcase
  most_convincing_rationales: {
    correct: boolean;
    label: string;
    // eslint-disable-next-line camelcase
    most_convincing: {
      id: number;
      times_chosen: number; // eslint-disable-line camelcase
      times_shown: number; // eslint-disable-line camelcase
      rationale: string;
    }[];
    text: string;
  };
  peer_impact: { score?: number | null; label: string }; // eslint-disable-line camelcase
  pk: number;
  text: string;
  title: string;
  type: string;
  urls?: {
    add_answer_choices: string; // eslint-disable-line camelcase
    add_new_question: string; // eslint-disable-line camelcase
    add_sample_answers: string; // eslint-disable-line camelcase
    copy_question: string; // eslint-disable-line camelcase
    fix: string;
  };
  user?: { username: string; saltise: boolean; expert: boolean };
  valid: boolean;
  video_url: string; // eslint-disable-line camelcase
};
