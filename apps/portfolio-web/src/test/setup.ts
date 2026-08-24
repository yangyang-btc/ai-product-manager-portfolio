import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

Object.defineProperty(window, 'scrollTo', { value: vi.fn(), writable: true })
Object.defineProperty(window, 'requestAnimationFrame', { value: (callback: FrameRequestCallback) => window.setTimeout(callback, 0), writable: true })
Object.defineProperty(Element.prototype, 'scrollIntoView', { value: vi.fn(), writable: true })

afterEach(() => {
  cleanup()
  window.location.hash = '#/'
})
