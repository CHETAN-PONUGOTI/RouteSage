
const fs = require('fs');
const content = fs.readFileSync('frontend/src/lib/api-client.ts', 'utf-8');

const additions = `
  async put<T>(endpoint: string, data: any, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string, options: Omit<RequestInit, 'method'> = {}): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
`;

const updatedContent = content.replace(
  "  async post<T>(endpoint: string, data: any, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {",
  additions + "\n  async post<T>(endpoint: string, data: any, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {"
);

fs.writeFileSync('frontend/src/lib/api-client.ts', updatedContent);
