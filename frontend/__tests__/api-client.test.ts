import { ApiClient, ApiError } from '../src/lib/api-client'

describe('ApiClient', () => {
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    originalFetch = global.fetch;
    process.env.NEXT_PUBLIC_API_URL = 'http://test-api.local';
  });

  afterEach(() => {
    global.fetch = originalFetch;
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('makes GET requests with correct URL', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' })
    });

    const client = new ApiClient();
    const result = await client.get('/health');

    expect(global.fetch).toHaveBeenCalledWith('http://test-api.local/health', expect.any(Object));
    expect(result).toEqual({ status: 'ok' });
  });

  it('throws ApiError on non-ok responses', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Resource not found' })
    });

    const client = new ApiClient();
    
    await expect(client.get('/missing')).rejects.toThrow(ApiError);
    await expect(client.get('/missing')).rejects.toHaveProperty('status', 404);
    await expect(client.get('/missing')).rejects.toHaveProperty('message', 'Resource not found');
  });
})
