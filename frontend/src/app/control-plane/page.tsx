import type { Metadata } from 'next';

import ContextControlPlane from '@/features/control-plane/ContextControlPlane';

export const metadata: Metadata = {
  title: 'Context Control Plane | OntoWiz',
  description: 'Synthetic domain-pack control plane for governed context, evaluation and agent simulation.',
};

export default function ControlPlanePage() {
  return <ContextControlPlane />;
}
