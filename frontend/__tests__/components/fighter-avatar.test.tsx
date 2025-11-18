/**
 * Tests for FighterAvatar component
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { FighterAvatar } from '@/components/fighter-avatar';

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

describe('FighterAvatar', () => {
  it('should render fallback icon when no src provided', () => {
    const { container } = render(<FighterAvatar alt="Test Fighter" />);
    const fallback = container.querySelector('.lucide-user');
    expect(fallback).toBeInTheDocument();
  });

  it('should render fallback icon when src is null', () => {
    const { container } = render(<FighterAvatar src={null} alt="Test Fighter" />);
    const fallback = container.querySelector('.lucide-user');
    expect(fallback).toBeInTheDocument();
  });

  it('should render image when src is provided', () => {
    render(<FighterAvatar src="https://example.com/fighter.jpg" alt="Test Fighter" />);
    const img = screen.getByRole('img');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('alt', 'Test Fighter');
  });

  it('should show fallback on image error', () => {
    const { container } = render(<FighterAvatar src="https://example.com/fighter.jpg" alt="Test Fighter" />);
    const img = screen.getByRole('img');

    // Trigger error
    fireEvent.error(img);

    // Should show fallback icon
    const fallback = container.querySelector('.lucide-user');
    expect(fallback).toBeInTheDocument();
  });

  it('should apply correct size classes', () => {
    const { container } = render(<FighterAvatar alt="Test Fighter" size="lg" />);
    const avatar = container.firstChild;
    expect(avatar).toHaveClass('w-24', 'h-24');
  });

  it('should use medium size by default', () => {
    const { container } = render(<FighterAvatar alt="Test Fighter" />);
    const avatar = container.firstChild;
    expect(avatar).toHaveClass('w-16', 'h-16');
  });

  it('should apply custom className', () => {
    const { container } = render(<FighterAvatar alt="Test Fighter" className="custom-class" />);
    const avatar = container.firstChild;
    expect(avatar).toHaveClass('custom-class');
  });

  it('should render different sizes correctly', () => {
    const sizes: Array<'sm' | 'md' | 'lg' | 'xl'> = ['sm', 'md', 'lg', 'xl'];
    const expectedClasses = {
      sm: ['w-12', 'h-12'],
      md: ['w-16', 'h-16'],
      lg: ['w-24', 'h-24'],
      xl: ['w-32', 'h-32'],
    };

    sizes.forEach((size) => {
      const { container } = render(<FighterAvatar alt="Test" size={size} />);
      const avatar = container.firstChild;
      expectedClasses[size].forEach((cls) => {
        expect(avatar).toHaveClass(cls);
      });
    });
  });

  it('should have rounded-full class', () => {
    const { container } = render(<FighterAvatar alt="Test Fighter" />);
    const avatar = container.firstChild;
    expect(avatar).toHaveClass('rounded-full');
  });

  it('should have proper gradient background for fallback', () => {
    const { container } = render(<FighterAvatar alt="Test Fighter" />);
    const avatar = container.firstChild;
    expect(avatar).toHaveClass('bg-gradient-to-br');
  });
});
