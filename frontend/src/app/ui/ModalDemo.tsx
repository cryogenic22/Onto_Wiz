'use client';

import { useState } from 'react';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';

/** Interactive Modal demo for the /ui gallery (Modal owns open state via a client wrapper). */
export default function ModalDemo() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button variant="secondary" onClick={() => setOpen(true)}>
        Open dialog
      </Button>
      <Modal open={open} onClose={() => setOpen(false)} title="Confirm release">
        <p className="text-[13px]">
          A dialog primitive on Foundry tokens — Escape, overlay click, and the close button
          all dismiss it.
        </p>
      </Modal>
    </>
  );
}
