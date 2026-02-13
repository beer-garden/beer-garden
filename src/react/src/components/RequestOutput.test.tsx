
import { render} from '@testing-library/react';
import { expect, test, describe } from 'vitest'
import RequestOutput from './RequestOutput'


describe('RequestOutput', () => {
    test('renders skeleton when status is CREATED', async () => {
        const page = render(
            <RequestOutput id="123" status="CREATED" output="" output_type="STRING" />
        );

        await expect(page.container.querySelector('#request-output-skeleton')).toBeVisible();
    })

    test('renders skeleton when status is IN_PROGRESS', async () => {
        const page = await render(
            <RequestOutput id="123" status="IN_PROGRESS" output="" output_type="STRING" />
        )
        
        await expect(page.container.querySelector('#request-output-skeleton')).toBeVisible();
    })

    test('renders STRING output when status is SUCCESS', async () => {
        const page = await render(
            <RequestOutput id="123" status="SUCCESS" output="Test output" output_type="STRING" />
        )
        await expect(page.container.querySelector('#request-output')).toBeVisible();
        await expect(page.getByText('Test output')).toBeVisible()
    })

    test('renders parsed JSON output', async () => {
        const page = await render(
            <RequestOutput id="123" status="SUCCESS" output='{"key":"value"}' output_type="JSON" />
        )
        await expect(page.container.querySelector('#request-output')).toBeVisible();
        await expect(page.getByText(/key/)).toBeVisible()
    })

    test('renders error message for invalid JSON', async () => {
        const page = await render(
            <RequestOutput id="123" status="SUCCESS" output="invalid json" output_type="JSON" />
        )
        await expect(page.container.querySelector('#request-output')).toBeVisible();
        await expect(page.getByText(/Failed to parse JSON/)).toBeVisible()
    })

    test('renders HTML output with dangerouslySetInnerHTML', async () => {
        const page = await render(
            <RequestOutput id="123" status="SUCCESS" output="<p>HTML content</p>" output_type="HTML" />
        )
        await expect(page.container.querySelector('#request-output')).toBeVisible();
        await expect(page.getByText('HTML content')).toBeVisible()
    })
})
