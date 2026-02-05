import { expect, test } from 'vitest'
import  RequestOutput  from './RequestOutput'
import { render } from 'vitest-browser-react'
// import { test, expect } from '@playwright/test';

test('RequestOutput renders correctly', async () => {
  const  requestOutput  = await render(<RequestOutput {...{ id: '123', status: "SUCCESS", output: 'Test output', output_type:'STRING'}} />);

//   await expect.element(screen.getByText('Test output')).toBeVisible()
  await expect.element(requestOutput).toHaveTextContent('hello there')
})

