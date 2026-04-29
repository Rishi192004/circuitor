import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

/**
 * Visual Language Enforcement Test
 * 
 * Ensures that Errors and Suggestions (Ghost Components) never share
 * the same color or animation styles, as per strict product requirements.
 */
describe('Visual Language Strict Separation', () => {
  const cssPath = path.resolve(__dirname, '../index.css');
  const cssContent = fs.readFileSync(cssPath, 'utf8');

  it('should not share colors between errors and suggestions', () => {
    // Extract variables
    const errorRed = cssContent.match(/--error-red:\s*(#[a-fA-F0-9]+|var\(--[a-zA-Z-]+\))/)?.[1];
    const suggestionBlue = cssContent.match(/--suggestion-blue:\s*(#[a-fA-F0-9]+|var\(--[a-zA-Z-]+\))/)?.[1];
    const suggestionPurple = cssContent.match(/--suggestion-purple:\s*(#[a-fA-F0-9]+|var\(--[a-zA-Z-]+\))/)?.[1];

    expect(errorRed).toBeDefined();
    expect(suggestionBlue).toBeDefined();
    expect(suggestionPurple).toBeDefined();

    expect(errorRed).not.toBe(suggestionBlue);
    expect(errorRed).not.toBe(suggestionPurple);
  });

  it('should only apply shake animation to errors', () => {
    // Check if animate-shake is used in proximity to ghost components
    const ghostNodeSection = cssContent.split('.ghost-node')[1];
    expect(ghostNodeSection).not.toContain('animate-shake');
    
    // Check if suggestion tokens are mixed with error tokens
    const errorSection = cssContent.match(/\.has-error[\s\S]*?}/)?.[0];
    expect(errorSection).not.toContain('suggestion');
  });

  it('should have distinct stroke styles (solid vs dashed)', () => {
    const ghostNodeStyles = cssContent.match(/\.ghost-node[\s\S]*?stroke-dasharray:\s*['"]?([\d\s]+)['"]?/)?.[1];
    // Error highlights are solid by default (none) or different dash
    expect(ghostNodeStyles).toBeDefined();
    expect(ghostNodeStyles).not.toBe('none');
  });
});
