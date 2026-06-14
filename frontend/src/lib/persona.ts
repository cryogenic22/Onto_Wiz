'use client';

import { createContext, useContext } from 'react';

export type PersonaMode = 'sme' | 'curator';

const PersonaContext = createContext<PersonaMode>('sme');

export const PersonaProvider = PersonaContext.Provider;

export function usePersona(): PersonaMode {
  return useContext(PersonaContext);
}
